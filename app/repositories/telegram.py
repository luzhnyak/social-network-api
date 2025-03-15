from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User
from app.models.telegram_account import TelegramAccount


class TelegramAccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def create_telegram_account(self, session_string: str, user_id: int, is_telegram_auth: bool) -> TelegramAccount:
        try:
            account = TelegramAccount(
                session_string=session_string, user_id=user_id, is_telegram_auth=False)
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            return account
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=str(e))

    def get_telegram_account(self, user_id: int) -> TelegramAccount:
        try:
            query = select(TelegramAccount).where(
                TelegramAccount.user_id == user_id)
            result = self.db.execute(query)
            telegram_account = result.scalars().first()
            if not telegram_account:
                return None
            return telegram_account
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=str(e))

    def update_telegram_account(self, session_string: str, user_id: int, is_telegram_auth: bool) -> TelegramAccount:
        try:
            account = self.get_telegram_account(user_id)

            account.session_string = session_string
            account.is_telegram_auth = is_telegram_auth

            self.db.commit()
            self.db.refresh(account)
            return account
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=str(e))

    def delete_telegram_account(self, user_id: int) -> TelegramAccount:
        try:
            account = self.get_telegram_account(user_id)

            self.db.delete(account)
            self.db.commit()

            return account
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=str(e))
