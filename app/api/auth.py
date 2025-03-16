from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.telegram_account import TelegramAccount
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token
from app.schemas.token import Token
from app.deps import get_current_user, get_db
from app.services.auth import AuthService

router = APIRouter()


def get_user_service(db: Session = Depends(get_db)):
    return AuthService(db)


@router.post("/register")
def register(user: UserCreate, service: AuthService = Depends(get_user_service)):
    new_user = service.register(user)
    access_token = create_access_token(data={"sub": new_user.email})
    return {"token": access_token, "token_type": "bearer", "message": "User created successfully"}


@router.post("/login", response_model=Token)
def login(data: UserLogin, service: AuthService = Depends(get_user_service)):
    return service.login(data)


@router.get("/refresh-user", response_model=UserResponse)
def refresh_user(user=Depends(get_current_user), service: AuthService = Depends(get_user_service)):
    account = service.refresh_user(user.id)

    is_telegram_auth = False

    if account:
        is_telegram_auth = account.is_telegram_auth

    access_token = create_access_token(data={"sub": user.email})
    return {"isTelegramAuth": is_telegram_auth, "token": access_token, "message": "Login successful"}
