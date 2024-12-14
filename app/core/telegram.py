import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from typing import List, Dict, Any


class TelegramAuthService:
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        # Зберігаємо додаткову інформацію про сесію
        self.phone_number = None
        self.phone_code_hash = None
        self.client = None

    async def create_client(self, session_string: str = None):
        """
        Створення нового клієнта Telegram
        """
        try:
            self.client = TelegramClient(
                StringSession(
                    session_string) if session_string else StringSession(),
                self.api_id,
                self.api_hash
            )
            await self.client.connect()
            return self.client
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def start_authorization(self, phone_number: str):
        """
        Ініціює процес авторизації та надсилає код підтвердження
        """
        try:
            # Створюємо нового клієнта
            await self.create_client()

            # Зберігаємо номер телефону
            self.phone_number = phone_number

            # Надсилаємо код
            send_code = await self.client.send_code_request(phone_number)

            self.phone_code_hash = send_code.phone_code_hash

            return {
                "status": "code_sent",
                "phone_number": phone_number,
                "phone_code_hash": send_code.phone_code_hash,
                "session_string": self.client.session.save()
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            # Закриваємо з'єднання, але не видаляємо клієнта
            if self.client:
                await self.client.disconnect()

    async def verify_phone_code(self, phone_number: str, phone_code: str, phone_code_hash: str, session_string: str = None):
        """
        Верифікує код підтвердження
        """
        try:
            await self.create_client(session_string)
            await self.client.sign_in(
                phone_number,
                phone_code,
                phone_code_hash=phone_code_hash
            )

            return {
                "status": "success",
                "session_string": self.client.session.save()
            }
        except SessionPasswordNeededError:
            return {
                "status": "2fa_required",
                "session_string": self.client.session.save()
            }
        except PhoneCodeInvalidError:
            raise HTTPException(
                status_code=400, detail="Invalid verification code")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            if self.client:
                await self.client.disconnect()

    async def verify_2fa_password(self, password: str, session_string: str = None):
        """
        Верифікує пароль двофакторної автентифікації
        """
        try:
            await self.create_client(session_string)
            await self.client.sign_in(password=password)
            return {
                "status": "success",
                "session_string": self.client.session.save()
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            if self.client:
                await self.client.disconnect()

    async def get_chats(self, session_string: str):
        """
        Отримання списку чатів з певної сесії
        """
        try:
            await self.create_client(session_string)
            chats = []
            async for dialog in self.client.iter_dialogs():
                chat = {
                    'id': dialog.id,
                    'name': dialog.name or 'Unnamed',
                    'type': dialog.entity.__class__.__name__,
                }
                chats.append(chat)
            return chats
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            if self.client:
                await self.client.disconnect()

    async def get_messages(self, session_string: str, chat_id: int, limit: int = 100):
        """
        Отримання повідомлень з конкретного чату

        :param chat_id: ID чату
        :param limit: Максимальна кількість повідомлень
        :return: Список повідомлень        
        """

        try:
            await self.create_client(session_string)

            messages = []
            async for message in self.client.iter_messages(chat_id, limit=limit):
                msg = {
                    'id': message.id,
                    'text': message.text or '',
                    'date': message.date.isoformat(),
                    'sender_id': message.sender_id,
                    'media': bool(message.media)
                }
                messages.append(msg)

            return messages

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            if self.client:
                await self.client.disconnect()

    async def logout(self, session_string: str):
        """
        Вихід з облікового запису

        :return: Успішність виходу
        """
        try:
            await self.create_client(session_string)
            if self.client:
                await self.client.log_out()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            if self.client:
                await self.client.disconnect()
