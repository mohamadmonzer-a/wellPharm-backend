import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from databases import Database
from sqlalchemy import Table, Column, Integer, String, Float, MetaData
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import httpx  # for Google token verification
import os
import secrets

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # IMPORTANT: replace in prod!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

database = Database(DATABASE_URL)
metadata = MetaData()

# Medicines table (existing)
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
    description: Optional[str] = None
    price: float
    image: Optional[str] = None

# Users table (existing)
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(100), unique=True, index=True, nullable=False),
    Column("hashed_password", String(200), nullable=False),
    Column("full_name", String(100), nullable=True),
)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class GoogleToken(BaseModel):
    token: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
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

@app.on_event("startup")
async def startup():
    await database.connect()
    # Note: create tables manually or via Alembic migrations

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/api/products", response_model=List[Medicine])
async def get_products():
    query = medicines.select()
    rows = await database.fetch_all(query)
    return [Medicine(**row) for row in rows]

@app.get("/")
async def root():
    return {"message": "FastAPI backend for wellPharm is running"}

@app.post("/api/register", response_model=UserOut)
async def register(user: UserCreate):
    query = users.select().where(users.c.email == user.email)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    insert_query = users.insert().values(
        email=user.email, hashed_password=hashed_password, full_name=user.full_name
    )
    user_id = await database.execute(insert_query)
    return {"id": user_id, "email": user.email, "full_name": user.full_name}

@app.post("/api/login", response_model=Token)
async def login(user: UserCreate):
    query = users.select().where(users.c.email == user.email)
    db_user = await database.fetch_one(query)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/google", response_model=Token)
async def google_auth(google_token: GoogleToken):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": google_token.token},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    token_info = resp.json()
    if token_info.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Invalid audience")

    email = token_info.get("email")
    full_name = token_info.get("name")

    query = users.select().where(users.c.email == email)
    user = await database.fetch_one(query)
    if not user:
        # Create user with a random password hash (Google login does not need password)
        random_password = secrets.token_urlsafe(16)
        hashed_password = get_password_hash(random_password)
        insert_query = users.insert().values(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )
        user_id = await database.execute(insert_query)
    else:
        user_id = user["id"]

    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}
