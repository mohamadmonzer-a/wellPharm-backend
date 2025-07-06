import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
from databases import Database
from sqlalchemy import Table, Column, Integer, String, Float, MetaData
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Load env vars
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # Replace with env var in prod
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

database = Database(DATABASE_URL)
metadata = MetaData()

# Medicines table & schema (your existing code)
medicines = Table(
    "medicines",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("description", String(500)),
    Column("price", Float, nullable=False),
    Column("image", String(200), nullable=True),
)

class Medicine(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    image: str | None = None

# New: Users table
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(100), unique=True, index=True, nullable=False),
    Column("hashed_password", String(200), nullable=False),
    Column("full_name", String(100), nullable=True),
)

# Auth utils
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Pydantic schemas for users & tokens
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

# FastAPI app and CORS middleware (your existing plus new origins if needed)
app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://well-pharm-frontend.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup/shutdown DB connection (your existing)
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Existing route: get products
@app.get("/api/products", response_model=List[Medicine])
async def get_products():
    query = medicines.select()
    rows = await database.fetch_all(query)
    return [Medicine(**row) for row in rows]

@app.get("/")
async def root():
    return {"message": "FastAPI backend for wellPharm is running"}

# New routes for user registration and login
@app.post("/api/register", response_model=UserOut)
async def register(user: UserCreate):
    query = users.select().where(users.c.email == user.email)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    query = users.insert().values(email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    user_id = await database.execute(query)
    return {"id": user_id, "email": user.email, "full_name": user.full_name}

@app.post("/api/login", response_model=Token)
async def login(user: UserCreate):
    query = users.select().where(users.c.email == user.email)
    db_user = await database.fetch_one(query)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}
