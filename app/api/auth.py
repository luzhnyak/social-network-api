from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.auth import UserCreate, UserLogin, UserResponse
from ..core.security import hash_password, verify_password
from ..core.jwt import create_access_token
from ..schemas.token import Token
from ..deps import get_current_user, get_db

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


@router.get("/refresh-user", response_model=UserResponse)
def refresh_user(db: Session = Depends(get_db), user=Depends(get_current_user)):
    access_token = create_access_token(data={"sub": user.email})
    return {"isTelegramAuth": False, "token": access_token, "message": "Login successful"}
