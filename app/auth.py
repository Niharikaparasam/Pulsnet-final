# app/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import sqlite3
from pathlib import Path
from typing import Optional, Literal
from app.config import DB_PATH, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# tokenUrl must match your login endpoint path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------- Pydantic Models ----------


class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    blood_group: Optional[str] = None
    role: str = "user" 
    
class Token(BaseModel):
    access_token: str
    token_type: str    

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    blood_group: Optional[str]
    created_at: str
    role: str                                     # 👈 new


# ---------- Database Setup ----------
def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        blood_group TEXT,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
       )
    """)

    conn.commit()
    conn.close()

init_db()

def get_db():
    # check_same_thread=False so SQLite works well with FastAPI
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Utility Functions ----------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_by_email(email: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

# ---------- Dependencies ----------
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user

# ---------- Routes ----------
@router.post("/signup", response_model=UserResponse)
async def signup(user: UserSignup):
    # Check if email already exists
    if get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    conn = get_db()
    cursor = conn.cursor()
    hashed_password = get_password_hash(user.password)

    try:
        cursor.execute("""
            INSERT INTO users (email, hashed_password, full_name, phone, blood_group, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user.email,
            hashed_password,
            user.full_name,
            user.phone,
            user.blood_group,
            user.role,             # 👈 from request
        ))

        conn.commit()
        user_id = cursor.lastrowid

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        new_user = cursor.fetchone()
        conn.close()

        return {
            "id": new_user["id"],
            "email": new_user["email"],
            "full_name": new_user["full_name"],
            "phone": new_user["phone"],
            "blood_group": new_user["blood_group"],
            "created_at": new_user["created_at"],
            "role": new_user["role"],
        }

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm uses 'username' field for login ID (here we treat it as email)
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "phone": current_user["phone"],
        "blood_group": current_user["blood_group"],
        "created_at": current_user["created_at"],
        "role": current_user["role"],
    }

async def require_hospital(current_user = Depends(get_current_user)):
    role = current_user["role"]
    if role != "hospital":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital accounts can access this resource."
        )
    return current_user


