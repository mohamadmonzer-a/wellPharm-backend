import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from databases import Database
from sqlalchemy import Table, Column, Integer, String, Float, MetaData
from dotenv import load_dotenv

load_dotenv()  # load .env file

DATABASE_URL = os.getenv("DATABASE_URL")

database = Database(DATABASE_URL)
metadata = MetaData()

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

app = FastAPI()

# Allow your frontend origin(s) here
origins = [
    "http://localhost:3000",           # frontend local dev
    "https://well-pharm-frontend.vercel.app/",  # deployed frontend domain
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
