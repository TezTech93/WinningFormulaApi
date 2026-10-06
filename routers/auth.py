# routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import bcrypt
import os
from typing import Optional
from jose import jwt, JWTError
import datetime
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings
from managers.user_manager import UserManager
from models.user import User, UserTier

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "khi-my-guy-always365")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ---------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    tier: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class AccessCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user_id = int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user_manager = UserManager(db)
    user = user_manager.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    print(f"📝 Registration attempt: {user_data.email}")

    user_manager = UserManager(db)

    existing = user_manager.get_user_by_email(user_data.email)
    if existing:
        print(f"❌ Email already registered: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = user_manager.get_user_by_username(user_data.username)
    if existing_username:
        print(f"❌ Username already taken: {user_data.username}")
        raise HTTPException(status_code=400, detail="Username already taken")

    try:
        user = user_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
        )
        print(f"✅ User created: {user.id} - {user.email}")

        access_token = create_access_token(data={"sub": str(user.id)})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "tier": user.tier.value,
            },
        }
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Login and return a JWT."""
    print(f"🔐 Login attempt: {login_data.email}")

    user_manager = UserManager(db)
    user = user_manager.authenticate_user(login_data.email, login_data.password)
    if not user:
        print(f"❌ Login failed: {login_data.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    print(f"✅ Login successful: {user.id} - {user.email}")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "tier": user.tier.value,
        },
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user=Depends(get_current_user),
):
    """Get current user info (basic fields)."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat(),
        "tier": current_user.tier.value,
    }


@router.post("/redeem-access-code")
async def redeem_access_code(
    body: AccessCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grants the current user Plus-tier access without going through Stripe.
    The submitted code must exactly match SUPERUSER_ACCESS_CODE.
    """
    expected = (settings.SUPERUSER_ACCESS_CODE or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Access codes are currently disabled")

    if body.code.strip() != expected:
        raise HTTPException(status_code=403, detail="Invalid access code")

    current_user.subscription_status = "active"
    current_user.subscription_tier = "plus"
    current_user.subscription_source = "access_code"
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Access code accepted",
        "subscription_status": current_user.subscription_status,
        "subscription_tier": current_user.subscription_tier,
        "subscription_source": current_user.subscription_source,
    }


@router.get("/login")
async def login_user_show():
    return {"message": "Login is working!"}


@router.get("/ping")
async def ping():
    """Sanity check that the router is mounted."""
    return {"message": "Auth router is mounted!", "status": "ok"}