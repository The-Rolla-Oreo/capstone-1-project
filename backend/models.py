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
    group_ids: list[str] = Field(default_factory=list)
    email_verified: bool = False
    profile_picture_url: str | None = None

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
    password: str = Field(..., min_length=10)
    email: str | None = None
    full_name: str | None = None
