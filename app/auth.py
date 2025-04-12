from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
import secrets
from uuid import uuid4
from .database import get_db
from .models import User, ConfirmationCode, LoginSession
from .schemas import (RegisterRequest, ConfirmRequest,
    CheckTelegramRequest, VerifyLoginRequest, LoginRequest)
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import hashlib
from bot import send_login_2fa_buttons
load_dotenv()

def hash_password(password: str) -> str:
    return hashlib.sha512(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

router = APIRouter(prefix="/api/auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mega-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "360")

@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(
        (User.email == request.email) |
        (User.phone == request.phone)
    ).first():
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=request.email,
        phone=request.phone,
        name=request.name,
        password_hash= hash_password(request.password)
    )
    code = str(secrets.randbelow(999999)).zfill(6)
    db.query(ConfirmationCode).filter(
        ConfirmationCode.email == request.email
    ).delete()
    db_code = ConfirmationCode(
        email=request.email,
        code=code
    )
    db.add(db_code)
    db.add(user)
    db.commit()

    return {
        "status": "success",
        "code": code,
        "link": f"https://t.me/flagship01_bot?start=reg_{code}"
    }

@router.post("/check-telegram")
async def check_telegram_auth(
    request: CheckTelegramRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram not linked"
        )

    token_data = {"sub": user.email}
    expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = jwt.encode(
        {"exp": datetime.now() + expires, **token_data},
        SECRET_KEY,
        ALGORITHM
    )

    return {"status": "success", "token": access_token}

@router.post("/login")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram not linked"
        )

    session_token = str(uuid4())
    login_session = LoginSession(
        user_id=user.id,
        session_token=session_token
    )
    db.add(login_session)
    db.commit()

    try:
        send_login_2fa_buttons(user.telegram_id, session_token)
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send confirmation request"
        )

    return {
        "status": "confirmation_required",
        "session_token": session_token,
        "message": "Please confirm login in Telegram"
    }

@router.post("/verify-login")
async def verify_login(
    request: VerifyLoginRequest,
    db: Session = Depends(get_db)
):
    login_session = db.query(LoginSession).filter(
        LoginSession.session_token == request.session_token,
        LoginSession.expires_at > datetime.now()
    ).first()

    if not login_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )

    if not login_session.is_confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Login not confirmed"
        )

    user = login_session.user
    token_data = {"sub": user.email}
    expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = jwt.encode(
        {"exp": datetime.now() + expires, **token_data},
        SECRET_KEY,
        ALGORITHM
    )

    db.delete(login_session)
    db.commit()

    return {"status": "success", "token": access_token}
