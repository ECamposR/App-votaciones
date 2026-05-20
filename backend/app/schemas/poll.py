from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.poll import VotingType, PollStatus


# --- VOTER GROUP SCHEMAS ---
class VoterGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class VoterGroupCreate(VoterGroupBase):
    pass


class VoterGroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    weight: float | None = Field(None, ge=0.0, le=1.0)


class VoterGroupRead(VoterGroupBase):
    id: uuid.UUID
    poll_id: uuid.UUID
    token: str

    model_config = {"from_attributes": True}


# --- CATEGORY SCHEMAS ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    order: int = Field(default=0, ge=0)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    order: int | None = Field(None, ge=0)


class CategoryRead(CategoryBase):
    id: uuid.UUID
    poll_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# --- OPTION SCHEMAS ---
class OptionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    photo_url: str | None = Field(None, max_length=1000)
    order: int = Field(default=0, ge=0)


class OptionCreate(OptionBase):
    category_id: uuid.UUID


class OptionRead(OptionBase):
    id: uuid.UUID
    poll_id: uuid.UUID
    category_id: uuid.UUID

    model_config = {"from_attributes": True}


# --- POLL SCHEMAS ---
class PollBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    voting_type: VotingType = Field(default=VotingType.PLURALITY)
    starts_at: datetime | None = Field(None)
    ends_at: datetime | None = Field(None)


class PollCreate(PollBase):
    pass


class PollUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    voting_type: VotingType | None = Field(None)
    starts_at: datetime | None = Field(None)
    ends_at: datetime | None = Field(None)


class PollRead(PollBase):
    id: uuid.UUID
    status: PollStatus
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PollStatusUpdate(BaseModel):
    status: PollStatus


# --- PUBLIC VOTING SCHEMAS ---
class PublicOptionRead(BaseModel):
    id: uuid.UUID
    name: str
    photo_url: str | None
    order: int

    model_config = {"from_attributes": True}


class PublicCategoryRead(BaseModel):
    id: uuid.UUID
    name: str
    order: int
    options: list[PublicOptionRead]

    model_config = {"from_attributes": True}


class PublicPollRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    voting_type: VotingType
    voter_group_name: str
    categories: list[PublicCategoryRead]
    already_voted: bool

    model_config = {"from_attributes": True}


class SingleVoteSubmit(BaseModel):
    category_id: uuid.UUID
    option_id: uuid.UUID


class VoteSubmit(BaseModel):
    votes: list[SingleVoteSubmit]
