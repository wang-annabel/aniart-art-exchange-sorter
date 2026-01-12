# app/db.py

import os
from collections.abc import AsyncGenerator
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, declared_attr
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from fastapi import Depends
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")


class Base(DeclarativeBase):
    pass


# Authentication User (matchmakers/admins)
class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = 'user'
    # SQLAlchemyBaseUserTableUUID provides:
    # - id (UUID, primary key)
    # - email (String, unique, indexed)
    # - hashed_password (String)
    # - is_active (Boolean)
    # - is_superuser (Boolean)
    # - is_verified (Boolean)

    name: Mapped[str | None] = mapped_column(String, nullable = True)

    # Use declared_attr for relationships on fastapi-users tables
    @declared_attr
    def created_matchings(cls) -> Mapped[list["Matching"]]:
        return relationship("Matching", back_populates = "creator", lazy = "selectin")


# Participants in art exchange (artists)
class Participant(Base):
    __tablename__ = 'participant'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), primary_key = True,
                                          default = uuid.uuid4)
    email: Mapped[str] = mapped_column(String, nullable = False, unique = True)
    name: Mapped[str] = mapped_column(String, nullable = False)
    discord: Mapped[str] = mapped_column(String, nullable = False)

    # Relationships
    drawn_for: Mapped[list["PreviouslyAssigned"]] = relationship(
        "PreviouslyAssigned",
        foreign_keys = "[PreviouslyAssigned.artist_id]",
        back_populates = "artist",
        lazy = "selectin"
    )
    received_from: Mapped[list["PreviouslyAssigned"]] = relationship(
        "PreviouslyAssigned",
        foreign_keys = "[PreviouslyAssigned.recipient_id]",
        back_populates = "recipient",
        lazy = "selectin"
    )


class PreviouslyAssigned(Base):
    __tablename__ = 'previously_assigned'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), primary_key = True,
                                          default = uuid.uuid4)
    artist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('participant.id'),
                                                 nullable = False)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True),
                                                    ForeignKey('participant.id'), nullable = False)
    assigned_date: Mapped[datetime] = mapped_column(DateTime, nullable = False,
                                                    default = datetime.now)
    matching_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid = True),
                                                          ForeignKey('matching.id'),
                                                          nullable = True)

    # Relationships
    artist: Mapped["Participant"] = relationship(
        "Participant",
        foreign_keys = [artist_id],
        back_populates = "drawn_for",
        lazy = "selectin"
    )
    recipient: Mapped["Participant"] = relationship(
        "Participant",
        foreign_keys = [recipient_id],
        back_populates = "received_from",
        lazy = "selectin"
    )
    matching: Mapped["Matching | None"] = relationship(
        "Matching",
        back_populates = "assignments",
        lazy = "selectin"
    )


class Matching(Base):
    """Stores confirmed matchings"""
    __tablename__ = 'matching'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), primary_key = True,
                                          default = uuid.uuid4)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid = True), ForeignKey('user.id'),
                                                  nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable = False, default = datetime.now)
    file_id: Mapped[str] = mapped_column(String, nullable = False)
    participant_count: Mapped[int] = mapped_column(Integer, nullable = False)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates = "created_matchings",
                                           lazy = "selectin")
    assignments: Mapped[list["PreviouslyAssigned"]] = relationship(
        "PreviouslyAssigned",
        back_populates = "matching",
        lazy = "selectin"
    )


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit = False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)