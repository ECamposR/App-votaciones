from __future__ import annotations

from app.database import Base
from app.models.user import AdminUser, AdminRole
from app.models.poll import Poll, VoterGroup, Category, Option, VotingType, PollStatus
from app.models.vote import Vote

# Esto facilita que Alembic descubra los modelos importando Base.metadata
__all__ = [
    "Base",
    "AdminUser",
    "AdminRole",
    "Poll",
    "VoterGroup",
    "Category",
    "Option",
    "VotingType",
    "PollStatus",
    "Vote",
]
