from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.jwt import create_access_token
from app.models.telegram_account import TelegramAccount
from app.schemas.telegram import PhoneAuthRequest, PhoneCodeVerifyRequest,  TwoFactorAuthRequest
from app.deps import get_current_user, get_db, get_telegram_service


router = APIRouter()


@router.post("/auth/start")
async def start_telegram_auth(request: PhoneAuthRequest, user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    """
    Початок процесу авторизації - надсилання коду підтвердження
    """
    result = await telegram_service.start_authorization(request.phone_number)
    return result


@router.post("/auth/verify-code")
async def verify_telegram_code(request: PhoneCodeVerifyRequest, db: Session = Depends(get_db), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    """
    Верифікація коду підтвердження 
    Повертає або сесію, або статус необхідності 2FA
    """
    print("result")
    result = await telegram_service.verify_phone_code(
        request.phone_number,
        request.phone_code,
        request.phone_code_hash,
        request.session_string
    )

    if result.get("status") == "success":
        account = TelegramAccount(
            session_string=result.get("session_string"), user_id=user.id)
        db.add(account)
        db.commit()
        db.refresh(account)

    return result


@router.post("/auth/verify-2fa")
async def verify_two_factor(request: TwoFactorAuthRequest, db: Session = Depends(get_db), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    """
    Верифікація паролю двофакторної автентифікації
    """
    result = await telegram_service.verify_2fa_password(request.password, request.session_string)

    if result.get("status") == "success":
        account = TelegramAccount(
            session_string=result.get("session_string"), user_id=user.id)
        db.add(account)
        db.commit()
        db.refresh(account)

    return result


@router.get("/chats")
async def get_chats_telegram(db: Session = Depends(get_db), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    account = db.query(TelegramAccount).filter(
        TelegramAccount.user_id == user.id).first()

    if not account or not account.is_telegram_auth:
        return {"status": "telegram_not_autorize", "message": "Telegram account not authorized"}

    result = await telegram_service.get_chats(account.session_string)

    return result


@router.get("/chats/{chat_id}/messages")
async def get_messages_telegram(chat_id: int, db: Session = Depends(get_db), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    account = db.query(TelegramAccount).filter(
        TelegramAccount.user_id == user.id).first()

    if not account or not account.is_telegram_auth:
        return {"status": "telegram_not_autorize", "message": "Telegram account not authorized"}

    result = await telegram_service.get_messages(chat_id, account.session_string)

    return result


@router.get("/disconnect")
async def disconnect_telegram(db: Session = Depends(get_db), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    account = db.query(TelegramAccount).filter(
        TelegramAccount.user_id == user.id).first()

    if not account or not account.is_telegram_auth:
        return {"status": "telegram_not_autorize", "message": "Telegram account not authorized"}

    telegram_service.logout(account.session_string)

    db.delete(account)
    db.commit()

    access_token = create_access_token(data={"sub": user.email})

    return {"isTelegramAuth": False, "token": access_token, "message": "Telegram account disconnected"}
