import os
import asyncio
from databases import Database
from sqlalchemy import Table, Column, Integer, String, MetaData
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("name", String(255)),
    Column("provider", String(50)),
    Column("provider_id", String(255)),
    Column("hashed_password", String(255), nullable=True),
)

async def reset_users_table():
    database = Database(DATABASE_URL)
    await database.connect()

    # Drop table if exists
    await database.execute("DROP TABLE IF EXISTS users CASCADE;")

    # Create table again
    query = """
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255),
        provider VARCHAR(50),
        provider_id VARCHAR(255),
        hashed_password VARCHAR(255)
    );
    """
    await database.execute(query)
    print("Dropped and recreated 'users' table successfully.")

    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(reset_users_table())
