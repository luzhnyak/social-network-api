from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.jwt import create_access_token
from models.telegram_account import TelegramAccount
from schemas.telegram import PhoneAuthRequest, PhoneCodeVerifyRequest,  TwoFactorAuthRequest
from deps import get_current_user, get_db, get_telegram_service


router = APIRouter()


@router.post("/auth/start")
async def start_telegram_auth(request: PhoneAuthRequest, db: Session = Depends(get_db), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    result = await telegram_service.start_authorization(request.phone_number)
    if result.get("status") == "code_sent":
        account = db.query(TelegramAccount).filter(
            TelegramAccount.user_id == user.id).first()

        if not account:
            account = TelegramAccount(
                session_string=result.get("session_string"), user_id=user.id, is_telegram_auth=False)
            db.add(account)

        account.session_string = result.get("session_string")
        account.is_telegram_auth = False

        db.commit()
        db.refresh(account)
    return result


@router.post("/auth/verify-code")
async def verify_telegram_code(request: PhoneCodeVerifyRequest, db: Session = Depends(get_db), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    result = await telegram_service.verify_phone_code(
        request.phone_number,
        request.phone_code,
        request.phone_code_hash,
        request.session_string
    )

    if result.get("status") == "success":
        account = db.query(TelegramAccount).filter(
            TelegramAccount.user_id == user.id).first()

        if not account:
            account = TelegramAccount(
                session_string=result.get("session_string"), user_id=user.id, is_telegram_auth=True)
            db.add(account)

        account.session_string = result.get("session_string")
        account.is_telegram_auth = True

        db.commit()
        db.refresh(account)

    return result


@router.post("/auth/verify-2fa")
async def verify_two_factor(request: TwoFactorAuthRequest, db: Session = Depends(get_db), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    result = await telegram_service.verify_2fa_password(request.password, request.session_string)

    if result.get("status") == "success":
        account = db.query(TelegramAccount).filter(
            TelegramAccount.user_id == user.id).first()

        if not account:
            account = TelegramAccount(
                session_string=result.get("session_string"), user_id=user.id, is_telegram_auth=True)
            db.add(account)

        account.session_string = result.get("session_string")
        account.is_telegram_auth = True

        db.commit()
        db.refresh(account)

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
