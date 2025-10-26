from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import HTTPException, Depends
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from starlette import status
from starlette.requests import Request

from backend.models import UserInDB, TokenData
from backend.settings import get_settings
from motor.motor_asyncio import AsyncIOMotorClient

settings = get_settings()

# JWT config
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]


password_hash = PasswordHash.recommended()


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str | None = None,
        scopes: dict | None = None,
        auto_error: bool = True,
    ) -> None:
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> str | None:
        authorization: str | None = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    """Verifies a plain password against a hashed password."""
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hashes a password using the recommended algorithm."""
    return password_hash.hash(password)


async def get_user(username: str) -> UserInDB | None:
    """Fetch a user document from MongoDB."""
    if users_coll is None:
        return None

    doc = await users_coll.find_one({"username": username})

    if doc:
        # Mongo returns _id but we ignore it for the model
        return UserInDB(**doc)

    return None


async def authenticate_user(username: str, password: str) -> UserInDB | None:
    """Authenticate a user by checking their username and password."""
    user = await get_user(username)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def create_access_token(data: dict, expires_delta_in_min: timedelta | None = None):
    """Create a JWT access token."""
    to_encode = data.copy()

    expire_timestamp = datetime.now(timezone.utc) + expires_delta_in_min

    to_encode.update({"exp": expire_timestamp})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """Get the current user from the JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user(token_data.username)

    if user is None:
        raise credentials_exception

    return user
