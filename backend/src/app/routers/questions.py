from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import *
from ..db import get_session
from ..services.ai_service import get_questions_ai_suggestions
from .auth import get_current_user




router = APIRouter()


@router.get("/vacancies/{vacancy_id}/questions_suggestions", tags=["Вопросы"], summary = "Получить подсказки вопросов от ИИ-ассистента", response_model=List[QuestionAISuggestion])
async def get_question_suggestions(vacancy_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
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





@router.post("/vacancies/{vacancy_id}/questions", tags=["Вопросы"], summary = "Добавить вопросы к вакансии по id", response_model=List[QuestionResponse])
async def add_questions_to_vacancy(
    vacancy_id: int,
    questions: List[QuestionCreate],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
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


@router.get("/questions", tags=["Вопросы"], summary = "Получить список всех вопросов", response_model=List[QuestionResponse])
async def get_all_questions(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
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



@router.delete("/questions/{question_id}", tags=["Вопросы"], summary = "Удалить вопрос", response_model=QuestionResponse)
async def delete_question(
    question_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
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





@router.put("/questions/{question_id}", tags=["Вопросы"], summary = "Обновить вопрос", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    updated_data: QuestionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
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