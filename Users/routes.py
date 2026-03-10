from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
import bcrypt
import psycopg2
from psycopg2 import pool
import os
from typing import Optional
import jwt
import datetime
from .manager import UserManager

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Database connection pool
DATABASE_URL = os.getenv("DATABASE_URL")
connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL)

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
    created_at: datetime.datetime
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
    created_at: datetime.datetime

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class UserTierUpdate(BaseModel):
    tier: str  # FREE, PAID, PLUS

# Helper functions
def get_db():
    """Get database connection from pool"""
    try:
        conn = connection_pool.getconn()
        yield conn
    finally:
        connection_pool.putconn(conn)

def get_user_manager(conn: psycopg2.extensions.connection = Depends(get_db)):
    return UserManager(conn)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Get current user from JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = user_manager.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Get user tier
    with user_manager.connection.cursor() as cursor:
        cursor.execute(
            "SELECT tier FROM users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        user["tier"] = result[0] if result else "FREE"
    
    return user

# Routes
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Register a new user"""
    # Check if user already exists
    existing_user = user_manager.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    password_hash = hash_password(user_data.password)
    
    try:
        user_id = user_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash
        )
        
        # Set default tier to FREE
        with user_manager.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET tier = 'FREE' WHERE id = %s",
                (user_id,)
            )
            user_manager.connection.commit()
        
        # Get created user
        user = user_manager.get_user_by_id(user_id)
        user["tier"] = "FREE"
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user_id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Login user and return access token"""
    # Get user by email
    user = user_manager.get_user_by_email(login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    with user_manager.connection.cursor() as cursor:
        cursor.execute(
            "SELECT password_hash FROM users WHERE id = %s",
            (user["id"],)
        )
        result = cursor.fetchone()
        if not result or not verify_password(login_data.password, result[0]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get user tier
        cursor.execute(
            "SELECT tier FROM users WHERE id = %s",
            (user["id"],)
        )
        tier_result = cursor.fetchone()
        user["tier"] = tier_result[0] if tier_result else "FREE"
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user["id"])})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.put("/me/password", status_code=status.HTTP_200_OK)
async def update_password(
    password_data: PasswordUpdate,
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Update user password"""
    # Verify current password
    with user_manager.connection.cursor() as cursor:
        cursor.execute(
            "SELECT password_hash FROM users WHERE id = %s",
            (current_user["id"],)
        )
        result = cursor.fetchone()
        if not result or not verify_password(password_data.current_password, result[0]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
    
    # Update password
    new_password_hash = hash_password(password_data.new_password)
    success = user_manager.update_user_password(current_user["id"], new_password_hash)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return {"message": "Password updated successfully"}

@router.post("/me/formulas", response_model=FormulaResponse, status_code=status.HTTP_201_CREATED)
async def add_formula(
    formula_data: FormulaCreate,
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Add a formula to user's collection"""
    # Check if user can add more formulas based on tier
    if not user_manager.can_add_formula(current_user["id"]):
        limit = user_manager.get_user_tier_limit(current_user["id"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User has reached maximum formula limit ({limit} formulas)"
        )
    
    # Add formula
    try:
        user_manager.add_user_formula(
            user_id=current_user["id"],
            formula_id=formula_data.formula_id,
            formula_name=formula_data.formula_name,
            formula=formula_data.formula
        )
        
        # Get the added formula
        formula = user_manager.get_formula_by_id(
            current_user["id"], 
            formula_data.formula_id
        )
        
        if formula:
            return formula
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Formula added but could not be retrieved"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding formula: {str(e)}"
        )

@router.get("/me/formulas", response_model=list[FormulaResponse])
async def get_user_formulas(
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Get all formulas for current user"""
    formulas = user_manager.get_user_formulas(current_user["id"])
    return formulas

@router.delete("/me/formulas/{formula_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_formula(
    formula_id: int,
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Delete a specific formula"""
    success = user_manager.delete_user_formula(current_user["id"], formula_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formula not found"
        )

# Admin routes (you might want to add admin authentication)
@router.put("/{user_id}/tier", response_model=UserResponse)
async def update_user_tier(
    user_id: int,
    tier_data: UserTierUpdate,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Update user tier (admin only)"""
    # In production, add admin authentication here
    
    if tier_data.tier not in ["FREE", "PAID", "PLUS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier. Must be FREE, PAID, or PLUS"
        )
    
    success = user_manager.update_user_tier(user_id, tier_data.tier)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return updated user
    user = user_manager.get_user_by_id(user_id)
    user["tier"] = tier_data.tier
    return user