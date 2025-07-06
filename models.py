from sqlalchemy import Table, Column, Integer, String, MetaData
from databases import Database

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("name", String(255)),
    Column("provider", String(50)),  # e.g., 'google', 'apple'
    Column("provider_id", String(255)),  # OAuth provider user id
    Column("hashed_password", String(255), nullable=True),  # for email/pass signup (optional)
)
