from collections.abc import AsyncGenerator
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi import Depends

DATABASE_URL = 'sqlite+aiosqlite:///./test.db'
# change for prod

class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    # a relationship to the previously assigned table?
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    pass

class PreviouslyAssigned(Base):
    __tablename__ = 'previously_assigned'
    artist_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    pass

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