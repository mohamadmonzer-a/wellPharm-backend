from sqlalchemy import Table, Column, Integer, String, MetaData
from databases import Database

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, index=True),
    Column("hashed_password", String),
    Column("full_name", String, nullable=True),
)
