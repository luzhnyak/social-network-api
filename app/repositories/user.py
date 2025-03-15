from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def create_user(self, str, email: str, hashed_password: str) -> User:
        try:
            if self.db.query(User).filter(User.email == email).first():
                raise HTTPException(
                    status_code=400, detail="Email already registered")

            new_user = User(email=email,
                            hashed_password=hashed_password)

            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            return new_user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=str(e))

    def get_user(self, user_id: int) -> User:
        try:
            query = select(User).where(User.id == user_id)
            result = self.db.execute(query)
            user = result.scalars().first()
            if not user:
                None
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=str(e))

    def get_user_by_email(self, email: str) -> User:
        try:
            query = select(User).where(User.email == email)
            result = self.db.execute(query)
            user = result.scalars().first()
            if not user:
                return None
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=str(e))
