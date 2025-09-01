from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from db import init_db, get_session
from models import Vacancy, VacancyCreate, VacancyResponse


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
    result = await session.execute(select(Vacancy))
    vacancies = result.scalars().all()
    return vacancies


@app.get("/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy_by_id_function(vacancy_id: int, session: AsyncSession = Depends(get_session)):
    vacancy = await session.get(Vacancy, vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail = "Vacancy not found")
    return vacancy


@app.post("/vacancies", response_model=VacancyResponse)
async def create_vacancy_function(vacancy: VacancyCreate, session: AsyncSession = Depends(get_session)):
    new_vacancy = Vacancy(**vacancy.dict())
    session.add(new_vacancy)
    await session.commit()
    await session.refresh(new_vacancy)
    return new_vacancy


