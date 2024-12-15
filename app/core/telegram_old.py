import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from typing import List, Dict, Any
import asyncio


class TelegramService:
    def __init__(self, api_id: int, api_hash: str):
        """
        Ініціалізація клієнта Telegram

        :param api_id: ID додатку з Telegram Developer Portal
        :param api_hash: Hash додатку з Telegram Developer Portal
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = None
        self.session = None

    async def create_client(self, phone_number: str) -> Dict[str, Any]:
        """
        Створення клієнта та надсилання коду верифікації

        :param phone_number: Номер телефону для авторизації
        :return: Словник з інформацією про статус авторизації
        """
        try:
            self.client = TelegramClient(
                StringSession(),
                self.api_id,
                self.api_hash
            )
            await self.client.connect()

            # Надсилання коду верифікації
            send_code = await self.client.send_code_request(phone_number)

            return {
                "status": "code_sent",
                "phone_code_hash": send_code.phone_code_hash
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def verify_code(self, phone_number: str, phone_code: str, phone_code_hash: str) -> Dict[str, Any]:
        """
        Верифікація коду та завершення авторизації

        :param phone_number: Номер телефону
        :param phone_code: Код верифікації
        :param phone_code_hash: Hash коду верифікації
        :return: Словник з результатом авторизації
        """
        try:
            await self.client.sign_in(
                phone_number,
                phone_code,
                phone_code_hash=phone_code_hash
            )
        except SessionPasswordNeededError:
            return {
                "status": "2fa_required",
                "message": "Необхідно ввести пароль двофакторної автентифікації"
            }

        # Збереження сесії
        self.session = self.client.session.save()

        return {
            "status": "authorized",
            "session": self.session
        }

    async def verify_2fa(self, password: str) -> Dict[str, Any]:
        """
        Верифікація двофакторної автентифікації

        :param password: Пароль 2FA
        :return: Словник з результатом авторизації
        """
        try:
            await self.client.sign_in(password=password)

            # Збереження сесії
            self.session = self.client.session.save()

            return {
                "status": "authorized",
                "session": self.session
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def restore_session(self, session_string: str) -> bool:
        """
        Відновлення раніше збереженої сесії

        :param session_string: Збережена сесія
        :return: Успішність відновлення сесії
        """
        try:
            self.client = TelegramClient(
                StringSession(session_string),
                self.api_id,
                self.api_hash
            )
            await self.client.connect()
            return True
        except Exception:
            return False

    async def get_chats(self) -> List[Dict[str, Any]]:
        """
        Отримання списку чатів

        :return: Список чатів з деталями
        """
        if not self.client:
            return []

        chats = []
        async for dialog in self.client.iter_dialogs():
            chat = {
                'id': dialog.id,
                'name': dialog.name or 'Unnamed',
                'type': dialog.entity.__class__.__name__,
                'unread_count': dialog.unread_count,
                'last_message': dialog.message.text if dialog.message else None
            }
            chats.append(chat)

        return chats

    async def get_messages(self, chat_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Отримання повідомлень з конкретного чату

        :param chat_id: ID чату
        :param limit: Максимальна кількість повідомлень
        :return: Список повідомлень
        """
        if not self.client:
            return []

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

    async def logout(self) -> bool:
        """
        Вихід з облікового запису

        :return: Успішність виходу
        """
        try:
            if self.client:
                await self.client.log_out()
            return True
        except Exception:
            return False

    async def close(self):
        """
        Закриття клієнта
        """
        if self.client:
            await self.client.disconnect()
            self.client = None
            self.session = None

# Приклад використання


async def main():
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')

    telegram_service = TelegramService(api_id, api_hash)

    # Процес авторизації
    auth_result = await telegram_service.create_client('+380972581000')

    print(auth_result['status'])
    code = input('Enter the code: ')

    if auth_result['status'] == 'code_sent':
        verification = await telegram_service.verify_code(
            '+380972581000',
            code,  # Код, отриманий користувачем
            auth_result['phone_code_hash']
        )
        print(verification['status'])
        if verification['status'] == '2fa_required':
            password = input('Enter the 2FA password: ')
            verification = await telegram_service.verify_2fa(password)
            print(verification['status'])
        else:
            print(auth_result['message'])

    # Отримання чатів
    chats = await telegram_service.get_chats()
    print(chats)

    # Отримання повідомлень конкретного чату
    # messages = await telegram_service.get_messages(chats[0]['id'])

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')

telegram_service = TelegramService(api_id, api_hash)

if __name__ == '__main__':
    asyncio.run(main())
