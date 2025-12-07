from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    # Expose MongoDB _id in API responses while accepting it from Mongo documents
    id: str | None = Field(
        default=None,
        serialization_alias="_id",
        validation_alias="_id",
    )
    username: str
    email: str | None = None
    full_name: str | None = None
    email_verified: bool = False
    profile_picture_url: str | None = None
    group_ids: list[str] = Field(default_factory=list)

    # Ensure Mongo's ObjectId gets serialized as a string
    @field_validator("id", mode="before")
    @classmethod
    def _convert_object_id(cls, v):
        if v is None:
            return v
        try:
            return str(v)
        except Exception:
            return v

    @field_validator("group_ids", mode="before")
    @classmethod
    def _convert_group_ids(cls, v):
        # normalize missing/None to empty list and ObjectId items to strings
        if v is None:
            return []
        try:
            return [str(item) for item in v]
        except Exception:
            return v


class UserInDB(User):
    hashed_password: str = Field(..., alias="hashed_password")


class UserCreate(BaseModel):
    """Payload for a new user."""
    username: str = Field(..., min_length=3, max_length=35)
    email: str | None = None
    full_name: str | None = None



class Group(BaseModel):
    """Model representing a household group."""
    id: str | None = Field(
        default=None,
        serialization_alias="_id",
        validation_alias="_id",
    )
    group_name: str = Field(..., min_length=5, max_length=35)
    group_admin_id: str
    group_admin_username: str
    users_in_group: list[str] = Field(default_factory=list)
    created_at: datetime | None = None

    @field_validator("id", mode="before")
    @classmethod
    def _convert_object_id(cls, v):
        if v is None:
            return v
        try:
            return str(v)
        except Exception:
            return v

    @field_validator("group_admin_id", mode="before")
    @classmethod
    def _convert_admin_id(cls, v):
        try:
            return str(v)
        except Exception:
            return v

    @field_validator("users_in_group", mode="before")
    @classmethod
    def _convert_user_ids(cls, v):
        if v is None:
            return []
        try:
            return [str(item) for item in v]
        except Exception:
            return v


class GroupCreate(BaseModel):
    """Payload for creating a new group."""
    group_name: str = Field(..., min_length=5, max_length=35)

class Chore(BaseModel):
    # Expose MongoDB _id in API responses while accepting it from Mongo documents
    id: str | None = Field(
        default=None,
        serialization_alias="_id",
        validation_alias="_id",
    )

    group_id: str | None = Field(
        default=None,
        serialization_alias="group_id",
        validation_alias="group_id",
    )

    chore_name: str
    chore_description: str
    assigned_user_id: str
    is_completed: bool = False
    created_at: datetime
    completed_at: datetime | None = None
    recurring_chore_id: str | None = Field(
        default=None,
        serialization_alias="group_id",
        validation_alias="group_id",
    )

    # Ensure Mongo's ObjectId gets serialized as a string
    @field_validator("id", "group_id", "recurring_chore_id", mode="before")
    @classmethod
    def _convert_object_id(cls, v):
        if v is None:
            return v
        try:
            return str(v)
        except Exception:
            return v


class RecurringChore(BaseModel):
    id: str | None = Field(
        default=None,
        serialization_alias="_id",
        validation_alias="_id",
    )

    group_id: str | None = Field(
        default=None,
        serialization_alias="group_id",
        validation_alias="group_id",
    )

    chore_name: str
    chore_description: str
    assigned_user_ids: list[str] = Field(default_factory=list)
    rrule: str
    start_date: datetime
    next_due_date: datetime
    is_active: bool = True
    last_assigned_user_index: int = 0
    created_at: datetime

    @field_validator("id", "group_id", mode="before")
    @classmethod
    def _convert_object_id(cls, v):
        if v is None:
            return v
        try:
            return str(v)
        except Exception:
            return v

    @field_validator("assigned_user_ids", mode="before")
    @classmethod
    def _convert_assigned_user_ids(cls, v):
        # normalize missing/None to empty list and ObjectId items to strings
        if v is None:
            return []
        try:
            return [str(item) for item in v]
        except Exception:
            return v
