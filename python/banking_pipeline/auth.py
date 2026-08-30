from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from banking_pipeline.config import load_settings

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class TokenUser(BaseModel):
    username: str
    role: str


def authenticate(username: str, password: str) -> TokenUser | None:
    settings = load_settings()
    for user in settings.users:
        if user.username == username and user.password == password:
            return TokenUser(username=user.username, role=user.role)
    return None


def create_token(user: TokenUser) -> str:
    settings = load_settings()
    payload = {
        "sub": user.username,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> TokenUser:
    settings = load_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    return TokenUser(username=str(payload["sub"]), role=str(payload["role"]))


def get_current_user(token: Annotated[str, Depends(oauth2)]) -> TokenUser:
    return decode_token(token)


def require_admin(user: Annotated[TokenUser, Depends(get_current_user)]) -> TokenUser:
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="ADMIN role required to run the batch")
    return user
