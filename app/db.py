import os
import uuid

from datetime import datetime
from collections.abc import AsyncGenerator

from fastapi import Depends

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from fastapi_users.db import (
    SQLAlchemyUserDatabase,
    SQLAlchemyBaseUserTableUUID,
)


# -----------------------------------------
# DATABASE CONFIGURATION
# -----------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./test.db"
)

# Convert PostgreSQL URL to asyncpg format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+asyncpg://",
        1
    )

elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1
    )


# -----------------------------------------
# DATABASE BASE CLASS
# -----------------------------------------

class Base(DeclarativeBase):
    pass


# -----------------------------------------
# USER MODEL
# -----------------------------------------

class User(SQLAlchemyBaseUserTableUUID, Base):
    posts = relationship(
        "Post",
        back_populates="user"
    )


# -----------------------------------------
# POST MODEL
# -----------------------------------------

class Post(Base):
    __tablename__ = "posts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False
    )

    caption = Column(Text)

    url = Column(
        String,
        nullable=False
    )

    file_type = Column(
        String,
        nullable=False
    )

    file_name = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship(
        "User",
        back_populates="posts"
    )


# -----------------------------------------
# DATABASE ENGINE
# -----------------------------------------

engine = create_async_engine(DATABASE_URL)

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False
)


# -----------------------------------------
# CREATE DATABASE TABLES
# -----------------------------------------

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -----------------------------------------
# ASYNC DATABASE SESSION
# -----------------------------------------

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# -----------------------------------------
# FASTAPI USERS DATABASE
# -----------------------------------------

async def get_user_db(
    session: AsyncSession = Depends(get_async_session)
):
    yield SQLAlchemyUserDatabase(session, User)