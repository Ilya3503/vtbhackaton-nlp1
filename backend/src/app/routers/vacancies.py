from fastapi import Depends, APIRouter, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlalchemy.orm import selectinload

from ..models import *
from ..db import get_session
from ..services.ai_service import generate_ai_vacancy_suggestions

from .auth import get_current_user




router = APIRouter()

@router.get("/vacancies", tags=["Получение и редактирование вакансий"], summary = "Получить список всех вакансий", response_model=List[VacancyResponse])
async def get_vacancies_function(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
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



@router.get("/vacancies/{vacancy_id}", tags=["Получение и редактирование вакансий"], summary = "Получить вакансию по id", response_model=VacancyResponse)
async def get_vacancy_by_id_function(vacancy_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
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



@router.post("/vacancies", tags=["Создание вакансии"], summary = "Создать вакансию", response_model=VacancyResponseAI)
async def create_vacancy_function(vacancy: VacancyCreate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):


    new_vacancy = Vacancy(
        vacancy_title=vacancy.vacancy_title,
        status="created",
        created_at=datetime.now(),
    )
    session.add(new_vacancy)
    await session.commit()
    await session.refresh(new_vacancy)


    ai_data = {"description": None, "requirements": None, "salary": None}
    try:
        ai_data = generate_ai_vacancy_suggestions(new_vacancy.vacancy_title)
    except Exception as e:
        print(f"AI suggestion error: {e}")


    return VacancyResponseAI(
        id=new_vacancy.id,
        vacancy_title=new_vacancy.vacancy_title,
        description=new_vacancy.description,
        requirements=new_vacancy.requirements,
        salary=new_vacancy.salary,
        status=new_vacancy.status,
        created_at=new_vacancy.created_at,
        questions=[],

        ai_description_suggestion=ai_data.get("description"),
        ai_requirements_suggestion=ai_data.get("requirements"),
        ai_salary_suggestion=ai_data.get("salary"),
    )



@router.put("/vacancies/{vacancy_id}", tags=["Получение и редактирование вакансий"], summary = "Обновить информацию о вакансии", response_model=VacancyResponse)
async def update_vacancy_function(vacancy_id: int, vacancy_data: VacancyUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
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



@router.delete("/vacancies/{vacancy_id}", tags=["Получение и редактирование вакансий"], summary = "Удалить вакансию", response_model=VacancyResponse)
async def delete_vacancy(vacancy_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
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


