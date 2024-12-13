from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.db import SessionLocal
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token
from app.schemas.token import Token
from app.deps import get_current_user, get_db

router = APIRouter()


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user.email,
                    hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = create_access_token(data={"sub": user.email})
    return {"token": access_token, "token_type": "bearer", "message": "User created successfully"}


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"token": access_token, "token_type": "bearer", "message": "Login successful"}
