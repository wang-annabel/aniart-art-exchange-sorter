from collections.abc import AsyncGenerator
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi import Depends
from datetime import datetime
DATABASE_URL = 'sqlite+aiosqlite:///./test.db'
# change for prod

class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)

    # foreign key relationships for previous assignments
    # artists this user has previously drawn for:
    drawn_for = relationship('PreviouslyAssigned',
                             foreign_keys='[PreviouslyAssigned.artist_id]',
                             back_populates='recipient')

    # artists this user has previously received from:
    received_from = relationship('PreviouslyAssigned',
                                 foreign_keys='[PreviouslyAssigned.recipient_id]',
                                 back_populates='requestor')

class PreviouslyAssigned(Base): # many-to-many
    __tablename__ = 'previously_assigned'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requestor_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    assigned_date = Column(DateTime, nullable=False, default=datetime.now())

    # relationships
    requestor = relationship('User', foreign_keys=[requestor_id], back_populates='received_from')
    recipient = relationship('User', foreign_keys=[recipient_id], back_populates='drawn_for')

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