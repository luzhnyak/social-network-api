from sqlalchemy import Column, Integer, String, ForeignKey
from app.db import Base


class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_string = Column(String, nullable=False)