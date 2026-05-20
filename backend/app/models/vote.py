from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.poll import Poll, VoterGroup, Category, Option


class Vote(Base):
    __tablename__ = "vote"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    poll_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("poll.id"), nullable=False)
    voter_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("voter_group.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id"), nullable=False)
    option_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("option.id"), nullable=False)
    
    # Identificador único del votante via cookie HttpOnly
    voter_token: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # IP del votante (para auditoría e identificación de spam)
    ip: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Para voto preferencial (Ranked Choice): indica el orden de preferencia (1, 2, 3...)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    # Relaciones
    poll: Mapped[Poll] = relationship(back_populates="votes")
    voter_group: Mapped[VoterGroup] = relationship(back_populates="votes")
    category: Mapped[Category] = relationship(back_populates="votes")
    option: Mapped[Option] = relationship(back_populates="votes")

    # Restricciones
    __table_args__ = (
        # Un votante no puede votar por la misma opción dos veces en el mismo grupo de un poll.
        # Esto permite voto preferencial (múltiples opciones rankeadas en una categoría)
        # pero evita que se repita la misma opción.
        UniqueConstraint(
            "poll_id",
            "voter_group_id",
            "voter_token",
            "option_id",
            name="uq_vote_voter_option",
        ),
    )
