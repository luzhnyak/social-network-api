from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_user_service
from app.core.jwt import create_access_token
from app.models.telegram_account import TelegramAccount
from app.schemas.telegram import PhoneAuthRequest, PhoneCodeVerifyRequest,  TwoFactorAuthRequest
from app.deps import get_current_user, get_db, get_telegram_service
from app.services.auth import AuthService


router = APIRouter()


@router.post("/auth/start")
async def start_telegram_auth(request: PhoneAuthRequest, service: AuthService = Depends(get_user_service), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    result = await telegram_service.start_authorization(request.phone_number)
    if result.get("status") == "code_sent":
        account = service.refresh_user(user.id)
        session_string = result.get("session_string")

        if not account:
            account = service.create_telegram_account(
                session_string, user.id, False)

        service.telegram_repo.update_telegram_account(
            session_string, user.id, False)

    return result


@router.post("/auth/verify-code")
async def verify_telegram_code(request: PhoneCodeVerifyRequest, service: AuthService = Depends(get_user_service), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    result = await telegram_service.verify_phone_code(
        request.phone_number,
        request.phone_code,
        request.phone_code_hash,
        request.session_string
    )

    if result.get("status") == "success":
        account = service.refresh_user(user.id)
        session_string = result.get("session_string")

        if not account:
            account = service.create_telegram_account(
                session_string, user.id, False)

        service.telegram_repo.update_telegram_account(
            session_string, user.id, True)

    return result


@router.post("/auth/verify-2fa")
async def verify_two_factor(request: TwoFactorAuthRequest, service: AuthService = Depends(get_user_service), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    result = await telegram_service.verify_2fa_password(request.password, request.session_string)

    if result.get("status") == "success":
        account = service.refresh_user(user.id)
        session_string = result.get("session_string")

        if not account:
            account = service.create_telegram_account(
                session_string, user.id, False)

        service.telegram_repo.update_telegram_account(
            session_string, user.id, True)

    return result


@router.get("/disconnect")
async def disconnect_telegram(service: AuthService = Depends(get_user_service), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    account = service.refresh_user(user.id)

    if not account or not account.is_telegram_auth:
        return {"status": "telegram_not_autorize", "message": "Telegram account not authorized"}

    telegram_service.logout(account.session_string)

    service.telegram_repo.delete_telegram_account(user.id)

    access_token = create_access_token(data={"sub": user.email})

    return {"isTelegramAuth": False, "token": access_token, "message": "Telegram account disconnected"}


@router.get("/chats")
async def get_chats_telegram(service: AuthService = Depends(get_user_service), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    account = service.refresh_user(user.id)

    if not account or not account.is_telegram_auth:
        return {"status": "telegram_not_autorize", "message": "Telegram account not authorized"}

    result = await telegram_service.get_chats(account.session_string)

    return result


@router.get("/chats/{chat_id}/messages")
async def get_messages_telegram(chat_id: int, service: AuthService = Depends(get_user_service), user=Depends(get_current_user), telegram_service=Depends(get_telegram_service)):
    account = service.refresh_user(user.id)

    if not account or not account.is_telegram_auth:
        return {"status": "telegram_not_autorize", "message": "Telegram account not authorized"}

    result = await telegram_service.get_messages(chat_id, account.session_string)

    return result
