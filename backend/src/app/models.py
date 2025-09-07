from sqlmodel import SQLModel, Field, Relationship
from typing import List
from datetime import datetime
from sqlalchemy.orm import selectinload
from typing import Optional

class User(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now)



# Базовая модель вакансии без ID (для создания)
class VacancyBase(SQLModel):
    vacancy_title: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary: Optional[int] = None
    status: str = Field(default="created")



# Модель вакансии ДЛЯ ТАБЛИЦЫ БД
class Vacancy(VacancyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # AI подсказки (nullable, строковые поля)
    ai_description_suggestion: Optional[str] = Field(default=None, sa_column=None)
    ai_requirements_suggestion: Optional[str] = Field(default=None, sa_column=None)
    ai_salary_suggestion: Optional[str] = Field(default=None, sa_column=None)
    # Опционально: кеш подсказок для вопросов (JSON строка)
    ai_questions_suggestions: Optional[str] = Field(default=None, sa_column=None)

    # СВЯЗЬ: у одной вакансии может быть много вопросов
    questions: List["Question"] = Relationship(back_populates="vacancy")



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
class VacancyCreate(SQLModel):
    vacancy_title: str

class QuestionResponse(SQLModel):
    id: int
    question_text: str
    competence: str
    weight: float

class QuestionUpdate(SQLModel):
    question_text: Optional[str] = None
    competence: Optional[str] = None
    weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)



class VacancyUpdate(SQLModel):
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary: Optional[int] = None
    status: Optional[str] = None


# Модель для ответа API (что возвращаем клиенту)
class VacancyResponse(VacancyBase):
    id: int
    created_at: datetime
    questions: List[QuestionResponse] = Field(default_factory=list)



class VacancyResponseAI(VacancyResponse):
    ai_description_suggestion: Optional[str] = None
    ai_requirements_suggestion: Optional[str] = None
    ai_salary_suggestion: Optional[int] = None



class QuestionAISuggestion(SQLModel):
    question_text: str
    competence: str
    weight: float
