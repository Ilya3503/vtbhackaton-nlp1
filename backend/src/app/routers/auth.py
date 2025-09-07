from authx import AuthX, AuthXConfig
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from ..db import get_session
from ..models import User



router = APIRouter()

config = AuthXConfig()
config.JWT_SECRET_KEY = "secret_key"
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]


security = AuthX(config=config)



class UserRegister(SQLModel):
    email: str
    password: str

class UserLogin(SQLModel):
    email: str
    password: str


async def get_current_user(session: AsyncSession = Depends(get_session)) -> User:
    # AuthX автоматически проверяет куки и декодирует токен
    user_id = await security.get_current_user()

    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/register")
async def register(user_data: UserRegister, session: AsyncSession = Depends(get_session)
):
    # Проверяем, нет ли уже такого email
    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Хешируем пароль
    hashed_password = security.password_hasher.hash(user_data.password)

    # Создаём пользователя
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        created_at=datetime.now()
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    # Создаём токен и устанавливаем в куки
    await security.set_access_cookie(str(user.id))

    return {"message": "User registered successfully", "user_id": user.id}




@router.post("/login")
async def login(
        user_data: UserLogin,
        session: AsyncSession = Depends(get_session)
):
    # Ищем пользователя
    user = session.exec(select(User).where(User.email == user_data.email)).first()

    if not user or not security.password_hasher.verify(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Устанавливаем токен в куки
    await security.set_access_cookie(str(user.id))

    return {"message": "Login successful", "user_id": user.id}



@router.post("/logout")
async def logout():
    await security.unset_access_cookie()
    return {"message": "Logout successful"}


# Эндпоинт получения текущего пользователя
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }