from fastapi import APIRouter, HTTPException, Depends, status
from backend.schemas.schemas import Token, UserLogin, UserOut
from backend.core.security import verify_password, create_access_token
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(payload: UserLogin):
    repo = SupplyGuardRepository()
    user = repo.users.get(payload.username)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user["username"], role=user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"]
    }

@router.get("/me", response_model=UserOut)
def get_current_user(username: str = "admin"):
    repo = SupplyGuardRepository()
    user = repo.users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"]
    }
