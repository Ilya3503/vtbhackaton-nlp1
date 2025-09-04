from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from sqlalchemy.orm import selectinload

from .db import init_db, get_session
from .models import Vacancy, VacancyCreate, QuestionResponse, VacancyResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="NLP HR Assistant",
    description="Backend для NLP-продукта по работе с вакансиями и резюме",
    lifespan=lifespan,
)



@app.get("/health_check")
def health_check_function():
    return {"health": "OK!"}



@app.get("/vacancies", response_model=List[VacancyResponse])
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



@app.get("/vacancies/{vacancy_id}", response_model=VacancyResponse)
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



@app.post("/vacancies", response_model=VacancyResponse)
async def create_vacancy_function(vacancy: VacancyCreate, session: AsyncSession = Depends(get_session)):
    new_vacancy = Vacancy(
        vacancy_title=vacancy.vacancy_title,
        status="created",
        created_at=datetime.now(),
    )
    session.add(new_vacancy)
    await session.commit()
    await session.refresh(new_vacancy)

    return VacancyResponse(
        id=new_vacancy.id,
        vacancy_title=new_vacancy.vacancy_title,
        description=new_vacancy.description,
        requirements=new_vacancy.requirements,
        salary=new_vacancy.salary,
        status=new_vacancy.status,
        created_at=new_vacancy.created_at,
        questions=[],
    )




@app.put("/vacancies/{vacancy_id}", response_model=VacancyResponse)
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
