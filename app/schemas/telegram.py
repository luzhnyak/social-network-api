from pydantic import BaseModel


class TelegramConnect(BaseModel):
    session_string: str
