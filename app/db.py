import os
from collections.abc import AsyncGenerator
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi import Depends
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print(f"DEBUG: DATABASE_URL = {os.getenv('DATABASE_URL')}")

DATABASE_URL = os.getenv('DATABASE_URL')

# Don't provide a fallback yet - let it fail if not set
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")

# DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./test.db')
# print('using url:', DATABASE_URL)
# 'sqlite+aiosqlite:///./test.db'
# change for prod

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'
    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    discord = Column(String, nullable=False)

    # foreign key relationships for previous assignments
    # artists this user has previously drawn for:
    drawn_for = relationship('PreviouslyAssigned',
                             foreign_keys='[PreviouslyAssigned.artist_id]',
                             back_populates='artist')

    # artists this user has previously received from:
    received_from = relationship('PreviouslyAssigned',
                                 foreign_keys='[PreviouslyAssigned.recipient_id]',
                                 back_populates='recipient')

class PreviouslyAssigned(Base): # many-to-many
    __tablename__ = 'previously_assigned'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    assigned_date = Column(DateTime, nullable=False, default=datetime.now())

    # relationships
    artist = relationship('User', foreign_keys=[artist_id], back_populates='drawn_for')
    recipient = relationship('User', foreign_keys=[recipient_id], back_populates='received_from')

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
async def get_user_db(session: AsyncSession=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)