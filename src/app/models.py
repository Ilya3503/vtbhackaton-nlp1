from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


# Базовая модель вакансии без ID (для создания)
class VacancyBase(SQLModel):
    vacancy_title: str
    description: str
    requirements: str
    salary: Optional[int] = None
    status: str = Field(default="created")


# Модель вакансии ДЛЯ ТАБЛИЦЫ БД
class Vacancy(VacancyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # СВЯЗЬ: у одной вакансии может быть много вопросов
    questions: Optional[List["Question"]] = Relationship(back_populates="vacancy")



# Модель вопроса ДЛЯ ТАБЛИЦЫ БД
class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question_text: str  # Текст вопроса
    competence: str  # Проверяемая компетенция
    weight: float = Field(ge=0.0, le=1.0)  # Вес (от 0 до 1)

    # ВНЕШНИЙ КЛЮЧ: связь с вакансией
    vacancy_id: int = Field(foreign_key="vacancy.id")

    # СВЯЗЬ: вопрос принадлежит одной вакансии
    vacancy: Optional[Vacancy] = Relationship(back_populates="questions")


# Модель для создания вопроса (тело запроса)
class QuestionCreate(SQLModel):
    question_text: str
    competence: str
    weight: float = Field(ge=0.0, le=1.0)


# Модель для создания вакансии (тело запроса)
class VacancyCreate(VacancyBase):
    pass


# Модель для ответа API (что возвращаем клиенту)
class VacancyResponse(VacancyBase):
    id: int
    created_at: datetime
    questions: List[QuestionCreate] = Field(default_factory=list)


