from pydantic import BaseModel


class UserResponse(BaseModel):
    isTelegramAuth: bool
    token: str
    message: str


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str
