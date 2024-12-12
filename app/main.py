from fastapi import FastAPI
from app.db import Base, engine
from app.api import auth, telegram

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(telegram.router, prefix="/telegram", tags=["Telegram"])
