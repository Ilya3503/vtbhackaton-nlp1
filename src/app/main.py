from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware

import asyncio

from sqlalchemy.orm import selectinload

from .db import init_db, get_session
from .models import (
    Vacancy,
    VacancyCreate,
    VacancyUpdate,
    VacancyResponse,
    VacancyResponseAI,
    Question,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionAISuggestion,
)
from .routers import nlp
from .services.ai_service import generate_ai_vacancy_suggestions, get_questions_ai_suggestions


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="NLP HR Assistant",
    description="Backend для NLP-продукта по работе с вакансиями и резюме",
    lifespan=lifespan,
    openapi_tags = [
        {"name": "Создание вакансии", "description": "Endpoints для создания вакансий: два способа"},
        {"name": "Получение и редактирование вакансий", "description": "Endpoints для работы с вакансиями"},
        {"name": "Вопросы", "description": "Endpoints для работы с вопросами"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nlp.router)



@app.get("/health_check")
def health_check_function():
    return {"health": "OK!"}



@app.get("/vacancies", tags=["Получение и редактирование вакансий"], summary = "Получить список всех вакансий", response_model=List[VacancyResponse])
async def get_vacancies_function(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Vacancy).options(selectinload(Vacancy.questions))
    )
    vacancies = result.scalars().all()

    return [
        VacancyResponse(
            id=vacancy.id,
            vacancy_title=vacancy.vacancy_title,
            description=vacancy.description,
            requirements=vacancy.requirements,
            salary=vacancy.salary,
            status=vacancy.status,
            created_at=vacancy.created_at,
            questions=[
                QuestionResponse(
                    id=q.id,
                    question_text=q.question_text,
                    competence=q.competence,
                    weight=q.weight
                )
                for q in vacancy.questions
            ]
        )
        for vacancy in vacancies
    ]



@app.get("/vacancies/{vacancy_id}", tags=["Получение и редактирование вакансий"], summary = "Получить вакансию по id", response_model=VacancyResponse)
async def get_vacancy_by_id_function(vacancy_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Vacancy)
        .where(Vacancy.id == vacancy_id)
        .options(selectinload(Vacancy.questions))
    )
    vacancy = result.scalar_one_or_none()

    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    return VacancyResponse(
        id=vacancy.id,
        vacancy_title=vacancy.vacancy_title,
        description=vacancy.description,
        requirements=vacancy.requirements,
        salary=vacancy.salary,
        status=vacancy.status,
        created_at=vacancy.created_at,
        questions=[
            QuestionResponse(
                id=q.id,
                question_text=q.question_text,
                competence=q.competence,
                weight=q.weight
            )
            for q in vacancy.questions
        ]
    )



@app.post("/vacancies", tags=["Создание вакансии"], summary = "Создать вакансию", response_model=VacancyResponseAI)
async def create_vacancy_function(vacancy: VacancyCreate, session: AsyncSession = Depends(get_session)):
    """
    Создает вакансию и возвращает AI-подсказки в одном ответе
    """
    # 1. Создаем и сохраняем вакансию
    new_vacancy = Vacancy(
        vacancy_title=vacancy.vacancy_title,
        status="created",
        created_at=datetime.now(),
    )
    session.add(new_vacancy)
    await session.commit()
    await session.refresh(new_vacancy)

    # 2. Получаем AI-подсказки (синхронный вызов)
    ai_data = {"description": None, "requirements": None, "salary": None}
    try:
        ai_data = generate_ai_vacancy_suggestions(new_vacancy.vacancy_title)
    except Exception as e:
        # Логируем ошибку, но не падаем - возвращаем null подсказки
        print(f"AI suggestion error: {e}")

    # 3. Возвращаем ответ с подсказками
    return VacancyResponseAI(
        id=new_vacancy.id,
        vacancy_title=new_vacancy.vacancy_title,
        description=new_vacancy.description,  # из БД (пока null)
        requirements=new_vacancy.requirements,  # из БД (пока null)
        salary=new_vacancy.salary,  # из БД (пока null)
        status=new_vacancy.status,
        created_at=new_vacancy.created_at,
        questions=[],  # пока нет вопросов

        # AI-подсказки
        ai_description_suggestion=ai_data.get("description"),
        ai_requirements_suggestion=ai_data.get("requirements"),
        ai_salary_suggestion=ai_data.get("salary"),
    )




@app.put("/vacancies/{vacancy_id}", tags=["Получение и редактирование вакансий"], summary = "Обновить информацию о вакансии", response_model=VacancyResponse)
async def update_vacancy_function(vacancy_id: int, vacancy_data: VacancyUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id).options(selectinload(Vacancy.questions))
    )
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    update_data = vacancy_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vacancy, key, value)

    await session.commit()
    await session.refresh(vacancy)

    return VacancyResponse(
        id=vacancy.id,
        vacancy_title=vacancy.vacancy_title,
        description=vacancy.description,
        requirements=vacancy.requirements,
        salary=vacancy.salary,
        status=vacancy.status,
        created_at=vacancy.created_at,
        questions=[
            QuestionResponse(
                id=q.id,
                question_text=q.question_text,
                competence=q.competence,
                weight=q.weight,
            )
            for q in vacancy.questions
        ],
    )


@app.delete("/vacancies/{vacancy_id}", tags=["Получение и редактирование вакансий"], summary = "Удалить вакансию", response_model=VacancyResponse)
async def delete_vacancy(
    vacancy_id: int,
    session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id).options(selectinload(Vacancy.questions))
    )
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    await session.delete(vacancy)
    await session.commit()

    return VacancyResponse(
        id=vacancy.id,
        vacancy_title=vacancy.vacancy_title,
        description=vacancy.description,
        requirements=vacancy.requirements,
        salary=vacancy.salary,
        status=vacancy.status,
        created_at=vacancy.created_at,
        questions=[
            QuestionResponse(
                id=q.id,
                question_text=q.question_text,
                competence=q.competence,
                weight=q.weight,
            )
            for q in vacancy.questions
        ],
    )





@app.get("/vacancies/{vacancy_id}/questions_suggestions", tags=["Вопросы"], summary = "Получить подсказки вопросов от ИИ-ассистента", response_model=List[QuestionAISuggestion])
async def get_question_suggestions(vacancy_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    try:
        ai_questions = get_questions_ai_suggestions(
            title=vacancy.vacancy_title or "",
            description=vacancy.description or "",
            requirements=vacancy.requirements or "",
        )
    except Exception as e:
        print(f"AI question suggestions error: {e}")
        return []

    return [QuestionAISuggestion(**q) for q in ai_questions]





@app.post("/vacancies/{vacancy_id}/questions", tags=["Вопросы"], summary = "Добавить вопросы к вакансии по id", response_model=List[QuestionResponse])
async def add_questions_to_vacancy(
    vacancy_id: int,
    questions: List[QuestionCreate],
    session: AsyncSession = Depends(get_session),
):
    # Проверяем, есть ли такая вакансия
    result = await session.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")

    created_questions = []
    for q in questions:
        new_question = Question(
            question_text=q.question_text,
            competence=q.competence,
            weight=q.weight,
            vacancy_id=vacancy_id,
        )
        session.add(new_question)
        created_questions.append(new_question)

    await session.commit()

    # Обновляем объекты после сохранения (чтобы получить id)
    for q in created_questions:
        await session.refresh(q)

    return [
        QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            competence=q.competence,
            weight=q.weight,
        )
        for q in created_questions
    ]


@app.get("/questions", tags=["Вопросы"], summary = "Получить список всех вопросов", response_model=List[QuestionResponse])
async def get_all_questions(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Question))
    questions = result.scalars().all()

    return [
        QuestionResponse(
            id=q.id,
            question_text=q.question_text,
            competence=q.competence,
            weight=q.weight,
        )
        for q in questions
    ]



@app.delete("/questions/{question_id}", tags=["Вопросы"], summary = "Удалить вопрос", response_model=QuestionResponse)
async def delete_question(
    question_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await session.delete(question)
    await session.commit()

    return QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        competence=question.competence,
        weight=question.weight,
    )





@app.put("/questions/{question_id}", tags=["Вопросы"], summary = "Обновить вопрос", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    updated_data: QuestionUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Обновляем поля
    question.question_text = updated_data.question_text
    question.competence = updated_data.competence
    question.weight = updated_data.weight

    session.add(question)
    await session.commit()
    await session.refresh(question)

    return QuestionResponse(
        id=question.id,
        question_text=question.question_text,
        competence=question.competence,
        weight=question.weight,
    )

