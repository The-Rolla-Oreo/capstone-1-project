from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None


class UserInDB(User):
    hashed_password: str = Field(..., alias="hashed_password")


class UserCreate(BaseModel):
    """Payload for a new user."""
    username: str = Field(..., min_length=3, max_length=35)
    password: str = Field(..., min_length=10)
    email: str | None = None
    full_name: str | None = None
