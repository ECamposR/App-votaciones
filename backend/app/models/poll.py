from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import AdminUser
    from app.models.vote import Vote


class VotingType(str, Enum):
    PLURALITY = "PLURALITY"
    RANKED = "RANKED"
    RATING = "RATING"
    YES_NO = "YES_NO"


class PollStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class Poll(Base):
    __tablename__ = "poll"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    voting_type: Mapped[VotingType] = mapped_column(default=VotingType.PLURALITY, nullable=False)
    status: Mapped[PollStatus] = mapped_column(default=PollStatus.DRAFT, index=True, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("admin_user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    created_by: Mapped[AdminUser] = relationship(back_populates="polls")
    voter_groups: Mapped[list[VoterGroup]] = relationship(
        back_populates="poll",
        cascade="all, delete-orphan",
    )
    categories: Mapped[list[Category]] = relationship(
        back_populates="poll",
        cascade="all, delete-orphan",
        order_by="Category.order",
    )
    options: Mapped[list[Option]] = relationship(
        back_populates="poll",
        cascade="all, delete-orphan",
        order_by="Option.order",
    )
    votes: Mapped[list[Vote]] = relationship(
        back_populates="poll",
        cascade="all, delete-orphan",
    )


class VoterGroup(Base):
    __tablename__ = "voter_group"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    poll_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("poll.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relaciones
    poll: Mapped[Poll] = relationship(back_populates="voter_groups")
    votes: Mapped[list[Vote]] = relationship(
        back_populates="voter_group",
        cascade="all, delete-orphan",
    )


class Category(Base):
    __tablename__ = "category"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    poll_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("poll.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    # Relaciones
    poll: Mapped[Poll] = relationship(back_populates="categories")
    options: Mapped[list[Option]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="Option.order",
    )
    votes: Mapped[list[Vote]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )


class Option(Base):
    __tablename__ = "option"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    poll_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("poll.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relaciones
    poll: Mapped[Poll] = relationship(back_populates="options")
    category: Mapped[Category] = relationship(back_populates="options")
    votes: Mapped[list[Vote]] = relationship(
        back_populates="option",
        cascade="all, delete-orphan",
    )
