from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
import bcrypt
import os
from typing import Optional
from jose import jwt, JWTError
import datetime
from .manager import UserManager

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Database path - can be set via environment variable
DB_PATH = os.getenv("SQLITE_DB_PATH", "winners_formula.db")

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str
    tier: Optional[str] = "FREE"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class FormulaCreate(BaseModel):
    formula_id: int
    formula_name: str
    formula: str

class FormulaResponse(BaseModel):
    id: int
    user_id: int
    formula_id: int
    formula_name: str
    formula: str
    created_at: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class UserTierUpdate(BaseModel):
    tier: str

# Helper functions
def get_user_manager():
    return UserManager(DB_PATH)

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
    user_manager: UserManager = Depends(get_user_manager)
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
    
    user = user_manager.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Routes
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_user(
    user_data: UserCreate,
    user_manager: UserManager = Depends(get_user_manager)
):
    # Prevent super user email from being used in registration
    if user_manager.is_super_user_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email reserved for super user")
    
    existing = user_manager.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = user_manager.get_user_by_username(user_data.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    password_hash = hash_password(user_data.password)
    try:
        user_id = user_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash
        )
        user = user_manager.get_user_by_id(user_id)
        access_token = create_access_token(data={"sub": str(user_id)})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "created_at": user["created_at"],
                "tier": user["tier"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    user_manager: UserManager = Depends(get_user_manager)
):
    print(f"Login attempt: {login_data.email}")
    
    # First check super users (plain text)
    super_user = user_manager.get_super_user_by_email(login_data.email)
    if super_user and super_user['password_hash'] == login_data.password:
        print("Super user authenticated")
        access_token = create_access_token(data={"sub": str(super_user["id"])})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": super_user["id"],
                "username": super_user["username"],
                "email": super_user["email"],
                "created_at": super_user["created_at"],
                "tier": super_user["tier"]
            }
        }
    
    # Then check normal users (bcrypt)
    user = user_manager.get_user_by_email(login_data.email)
    if user:
        conn = user_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
        result = cursor.fetchone()
        if result and verify_password(login_data.password, result[0]):
            print("Normal user authenticated")
            access_token = create_access_token(data={"sub": str(user["id"])})
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "created_at": user["created_at"],
                    "tier": user["tier"]
                }
            }
    
    print("Authentication failed")
    raise HTTPException(status_code=401, detail="Invalid email or password")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "created_at": current_user["created_at"],
        "tier": current_user["tier"]
    }

@router.put("/me/password", status_code=200)
async def update_password(
    password_data: PasswordUpdate,
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    # Super users cannot update password through this endpoint (they don't have db entry)
    if user_manager.is_super_user_email(current_user["email"]):
        raise HTTPException(status_code=400, detail="Super user password cannot be changed here")
    
    conn = user_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (current_user["id"],))
    result = cursor.fetchone()
    if not result or not verify_password(password_data.current_password, result[0]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    new_hash = hash_password(password_data.new_password)
    success = user_manager.update_user_password(current_user["id"], new_hash)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    return {"message": "Password updated successfully"}

@router.post("/me/formulas", response_model=FormulaResponse, status_code=201)
async def add_formula(
    formula_data: FormulaCreate,
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    user_id = current_user["id"]
    if not user_manager.can_add_formula(user_id):
        limit = user_manager.get_user_tier_limit(user_id)
        raise HTTPException(status_code=400, detail=f"Formula limit reached ({limit})")
    
    try:
        user_manager.add_user_formula(
            user_id=user_id,
            formula_id=formula_data.formula_id,
            formula_name=formula_data.formula_name,
            formula=formula_data.formula
        )
        # Retrieve the newly added formula (last one for this user)
        formulas = user_manager.get_user_formulas(user_id)
        new_formula = formulas[0] if formulas else None
        if not new_formula:
            raise HTTPException(status_code=500, detail="Formula added but could not be retrieved")
        return {
            "id": new_formula["id"],
            "user_id": new_formula["user_id"],
            "formula_id": new_formula["formula_id"],
            "formula_name": new_formula["formula_name"],
            "formula": new_formula["formula"],
            "created_at": new_formula["created_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding formula: {str(e)}")

@router.get("/me/formulas", response_model=list[FormulaResponse])
async def get_user_formulas(
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    formulas = user_manager.get_user_formulas(current_user["id"])
    return [
        {
            "id": f["id"],
            "user_id": f["user_id"],
            "formula_id": f["formula_id"],
            "formula_name": f["formula_name"],
            "formula": f["formula"],
            "created_at": f["created_at"]
        }
        for f in formulas
    ]

@router.delete("/me/formulas/{formula_record_id}", status_code=204)
async def delete_formula(
    formula_record_id: int,
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    success = user_manager.delete_user_formula(current_user["id"], formula_record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Formula not found")

# Admin routes
@router.put("/{user_id}/tier", response_model=UserResponse)
async def update_user_tier(
    user_id: int,
    tier_data: UserTierUpdate,
    user_manager: UserManager = Depends(get_user_manager)
):
    if tier_data.tier not in ["FREE", "PAID", "PLUS"]:
        raise HTTPException(status_code=400, detail="Invalid tier")
    # Super users cannot have tier updated via this endpoint (they are already PLUS)
    if user_manager.is_super_user_email(user_manager.get_user_by_id(user_id)["email"]):
        raise HTTPException(status_code=400, detail="Cannot update super user tier")
    success = user_manager.update_user_tier(user_id, tier_data.tier)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_manager.get_user_by_id(user_id)
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"],
        "tier": tier_data.tier
    }