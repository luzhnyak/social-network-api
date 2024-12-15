from pydantic import BaseModel


class PhoneAuthRequest(BaseModel):
    phone_number: str


class PhoneCodeVerifyRequest(BaseModel):
    phone_number: str
    phone_code: str
    phone_code_hash: str
    session_string: str


class TwoFactorAuthRequest(BaseModel):
    password: str
    session_string: str
