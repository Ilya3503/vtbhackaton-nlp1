from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
import docx
import re

from ..models import VacancyCreate, Vacancy, User
from ..db import get_session
from .auth import get_current_user

router = APIRouter()

async def parse_docx_to_vacancy(file) -> dict:
    try:
        doc = docx.Document(file)
    except Exception:
        raise HTTPException(status_code=400, detail="Не удалось открыть DOCX файл")

    data = {}
    for table in doc.tables:
        for row in table.rows:
            if len(row.cells) == 2:
                key = row.cells[0].text.strip()
                val = row.cells[1].text.strip()
                if key and val:
                    data[key] = val

    title = data.get("Название", "Без названия")
    status = data.get("Статус", "created")
    description = data.get("Обязанности (для публикации)", "")
    requirements = data.get("Требования (для публикации)", "")

    salary_text = (
        data.get("Доход (руб/мес)", "")
        or data.get("Оклад макс. (руб/мес)", "")
        or data.get("Оклад мин. (руб/мес)", "")
    )
    salary = None
    if salary_text:
        match = re.search(r"\d+", salary_text.replace(" ", ""))
        if match:
            salary = int(match.group())

    return {
        "vacancy_title": title,
        "description": description,
        "requirements": requirements,
        "salary": salary,
        "status": status
    }

# ---------------------------
# Эндпоинт: загрузка DOCX и сохранение в базу
# ---------------------------
@router.post("/nlp/upload-vacancy", tags=["Создание вакансии"], summary = "Загрузить вакансию файлом docx", response_model=VacancyCreate)
async def upload_vacancy(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Только .docx файлы поддерживаются")

    vacancy_data = await parse_docx_to_vacancy(file.file)
    vacancy = Vacancy(**vacancy_data)

    session.add(vacancy)
    await session.commit()
    await session.refresh(vacancy)

    return vacancy
