import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from databases import Database
from sqlalchemy import Table, Column, Integer, String, Float, MetaData
from dotenv import load_dotenv

load_dotenv()  # load .env

DATABASE_URL = os.getenv("DATABASE_URL")

database = Database(DATABASE_URL)
metadata = MetaData()

medicines = Table(
    "medicines",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("description", String(500)),
    Column("price", Float),
    Column("image", String(200), nullable=True),
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourfrontenddomain.com", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Medicine(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image: str = None

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
