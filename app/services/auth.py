from fastapi import HTTPException, status
from passlib.context import CryptContext
from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.models.telegram_account import TelegramAccount
from app.repositories.telegram import TelegramAccountRepository
from app.repositories.user import UserRepository
from app.schemas.auth import UserCreate, UserLogin, UserResponse
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.telegram_repo = TelegramAccountRepository(db)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def register(self, user: UserCreate):
        hashed_password = self.get_password_hash(user.password)

        if self.user_repo.get_user_by_email(user.email):
            raise HTTPException(
                status_code=409, detail="Email already registered")

        return self.user_repo.create_user(user.email, hashed_password)

    def login(self, data: UserLogin):
        user = self.user_repo.get_user_by_email(data.email)

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(data={"sub": user.email})
        return {"token": access_token, "token_type": "bearer", "message": "Login successful"}

    def refresh_user(self, user_id: int):
        return self.telegram_repo.get_telegram_account(user_id)

    def create_telegram_account(self, session_string: str, user_id: int, is_telegram_auth: bool) -> TelegramAccount:
        return self.telegram_repo.create_telegram_account(session_string, user_id, is_telegram_auth)

    def update_telegram_account(self, session_string: str, user_id: int, is_telegram_auth: bool) -> TelegramAccount:
        return self.telegram_repo.update_telegram_account(session_string, user_id, is_telegram_auth)

    def delete_telegram_account(self, user_id: int) -> TelegramAccount:
        return self.telegram_repo.delete_telegram_account(user_id)
