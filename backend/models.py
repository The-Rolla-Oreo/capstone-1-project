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


class UserInDB(User):
    hashed_password: str = Field(..., alias="hashed_password")


class UserCreate(BaseModel):
    """Payload for a new user."""
    username: str = Field(..., min_length=3, max_length=35)
    password: str = Field(..., min_length=10)
    email: str | None = None
    full_name: str | None = None
