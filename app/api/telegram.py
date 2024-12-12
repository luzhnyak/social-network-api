from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.telegram_account import TelegramAccount
from app.schemas.telegram import TelegramConnect
from app.deps import get_current_user, get_db

router = APIRouter()


@router.post("/connect")
def connect_telegram(data: TelegramConnect, db: Session = Depends(get_db), user=Depends(get_current_user)):
    account = TelegramAccount(
        session_string=data.session_string, user_id=user.id)
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"message": "Telegram account connected"}


@router.post("/disconnect")
def disconnect_telegram(db: Session = Depends(get_db), user=Depends(get_current_user)):
    account = db.query(TelegramAccount).filter(
        TelegramAccount.user_id == user.id).first()
    if not account:
        raise HTTPException(
            status_code=404, detail="Telegram account not found")
    db.delete(account)
    db.commit()
    return {"message": "Telegram account disconnected"}
