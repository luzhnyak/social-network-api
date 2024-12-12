from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.telegram_account import TelegramAccount
from app.schemas.telegram import TelegramConnect

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/connect")
def connect_telegram(data: TelegramConnect, db: Session = Depends(get_db)):
    # Replace user_id with current user
    new_account = TelegramAccount(
        session_string=data.session_string, user_id=1)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return {"message": "Telegram account connected"}


@router.post("/disconnect")
def disconnect_telegram(db: Session = Depends(get_db)):
    account = db.query(TelegramAccount).filter(
        TelegramAccount.user_id == 1).first()  # Replace with current user
    if not account:
        raise HTTPException(
            status_code=404, detail="Telegram account not found")
    db.delete(account)
    db.commit()
    return {"message": "Telegram account disconnected"}
