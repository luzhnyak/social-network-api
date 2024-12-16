from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import Base, engine
from api import auth, telegram

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Дозволити CORS
app.add_middleware(
    CORSMiddleware,
    # Додайте домен вашого фронтенду
    allow_origins=["http://localhost:3000",
                   "https://telegram.luzhnyak-dev.pp.ua"],
    allow_credentials=True,
    allow_methods=["*"],  # Дозволити всі HTTP-методи
    allow_headers=["*"],  # Дозволити всі заголовки
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(telegram.router, prefix="/telegram", tags=["Telegram"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8099)
