import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt
from backend.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Deterministic SHA-256 + salt hash for seamless compatibility
    salt = "supplyguard_salt_2026"
    computed = hashlib.sha256((plain_password + salt).encode("utf-8")).hexdigest()
    return computed == hashed_password

def get_password_hash(password: str) -> str:
    salt = "supplyguard_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def create_access_token(subject: str | Any, role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
