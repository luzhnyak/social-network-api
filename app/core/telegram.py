from fastapi import HTTPException
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError


class TelegramAuthService:
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash

        self.phone_number = None
        self.phone_code_hash = None
        self.client = None

    async def create_client(self, session_string: str = None):
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
        try:
            await self.create_client()

            self.phone_number = phone_number
            send_code = await self.client.send_code_request(phone_number)
            self.phone_code_hash = send_code.phone_code_hash

            return {
                "status": "code_sent",
                "phone_number": phone_number,
                "phone_code_hash": send_code.phone_code_hash,
                "session_string": self.client.session.save()
            }
        except Exception as e:
            print("====== Error in start_authorization ======", e)
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            if self.client:
                await self.client.disconnect()

    async def verify_phone_code(self, phone_number: str, phone_code: str, phone_code_hash: str, session_string: str = None):
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
        try:
            await self.create_client(session_string)
            chats = []
            async for dialog in self.client.iter_dialogs():
                last_message = dialog.message
                sender_name = None

                if last_message and last_message.sender:
                    if hasattr(last_message.sender, 'first_name') or hasattr(last_message.sender, 'last_name'):
                        sender_name = f"{last_message.sender.first_name or ''} {
                            last_message.sender.last_name or ''}".strip()
                    elif hasattr(last_message.sender, 'title'):
                        sender_name = last_message.sender.title
                    else:
                        sender_name = last_message.sender.username or "Unknown"

                chat = {
                    'id': dialog.id,
                    'name': dialog.name or 'Unnamed',
                    'type': dialog.entity.__class__.__name__,
                    'last_message': {
                        'id': last_message.id if last_message else None,
                        'text': last_message.text if last_message and last_message.text else None,
                        'date': last_message.date if last_message else None,
                        'sender_id': last_message.sender_id if last_message else None,
                        'sender': sender_name,
                    }
                }
                chats.append(chat)
            return chats
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            if self.client:
                await self.client.disconnect()

    async def get_messages(self, chat_id: int,  session_string: str,  limit: int = 100):
        try:
            await self.create_client(session_string)

            messages = []
            async for message in self.client.iter_messages(chat_id, limit=limit):

                sender_name = None
                if message.sender:
                    sender_name = f"{message.sender.first_name or ''} {
                        message.sender.last_name or ''}".strip() or message.sender.username or "Unknown"

                msg = {
                    'id': message.id,
                    'text': message.text or '',
                    'date': message.date.isoformat(),
                    'sender_id': message.sender_id,
                    'sender': sender_name,
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
        try:
            await self.create_client(session_string)
            if self.client:
                await self.client.log_out()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            if self.client:
                await self.client.disconnect()
