from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import selectinload

from .db import init_db
from .routers import nlp, vacancies, questions, auth

from .routers.auth import security



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="NLP HR Assistant",
    description="Backend для NLP-продукта по работе с вакансиями и резюме",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Создание вакансии", "description": "Endpoints для создания вакансий: два способа"},
        {"name": "Получение и редактирование вакансий", "description": "Endpoints для работы с вакансиями"},
        {"name": "Вопросы", "description": "Endpoints для работы с вопросами"},
        {"name": "Auth", "description": "Аутентификация и регистрация"},
    ],
    swagger_ui_init_oauth={
        "clientId": "your-client-id",
        "appName": "NLP HR Assistant"
    }
)




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nlp.router)
app.include_router(vacancies.router)
app.include_router(questions.router)
app.include_router(auth.router)



@app.get("/health_check")
def health_check_function():
    return {"health": "OK!"}























