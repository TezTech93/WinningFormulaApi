# routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
import bcrypt
import os
from typing import Optional
from jose import jwt, JWTError
import datetime

# Import the original manager (NOT the SQLAlchemy version)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Users.manager import UserManager, UserTier

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "khi-my-guy-always365")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str  # Changed from EmailStr to avoid validation issues
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

# Helper functions
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
    credentials: HTTPAuthorizationCredentials = Depends(security)
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
    
    # Use the original manager with super users
    user_manager = UserManager()
    user = user_manager.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_user(user_data: UserCreate):
    """
    Register a new user using the original manager
    """
    print(f"Registration attempt: {user_data.email}")
    
    # Use the original manager
    user_manager = UserManager()
    
    # Check if super user (prevent registration of super user emails)
    if user_manager.is_super_user_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email reserved for super user")
    
    # Check if email already exists
    existing = user_manager.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username already exists
    existing_username = user_manager.get_user_by_username(user_data.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    try:
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user
        user_id = user_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash
        )
        
        # Get the created user
        user = user_manager.get_user_by_id(user_id)
        
        # Create access token
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
    except Exception as e:
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """
    Login user using the original manager
    """
    print(f"Login attempt: {login_data.email}")
    
    # Use the original manager
    user_manager = UserManager()
    
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
        # Get the password hash from database
        conn = user_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
        result = cursor.fetchone()
        conn.close()
        
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
async def get_current_user_info(current_user = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "created_at": current_user["created_at"],
        "tier": current_user["tier"]
    }

@router.get("/ping")
async def ping():
    return {"message": "Auth router is mounted!", "status": "ok", "using": "original_manager"}