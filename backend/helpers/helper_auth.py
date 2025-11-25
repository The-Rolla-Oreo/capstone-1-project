import base64
import secrets
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

from backend.helpers.helper_email import send_email
from backend.models import UserInDB, TokenData
from backend.settings import get_settings
from pymongo import AsyncMongoClient

settings = get_settings()

# JWT config
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION
PASSWORD_RESET_COLLECTION = settings.PASSWORD_RESET_COLLECTION
EMAIL_VERIFICATION_COLLECTION = settings.EMAIL_VERIFICATION_COLLECTION

# Initialize MongoDB client
client = AsyncMongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]
password_reset_coll = _db[PASSWORD_RESET_COLLECTION]
email_verification_coll = _db[EMAIL_VERIFICATION_COLLECTION]


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


async def forgot_password_requested(email: str):
    # Note: We don't let user know if email exists so we can prevent account enumeration attacks

    # Make sure the user exists
    user_exists = await users_coll.find_one({"email": email})
    if not user_exists:
        return

    # Make sure the user has not already requested a password reset
    already_requested = await password_reset_coll.find_one({"email": email})
    if already_requested:
        return

    # Generate a random URL-safe string and store it in MongoDB
    random_bytes = secrets.token_bytes(64)
    url_safe_string = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    await password_reset_coll.insert_one({"email": email, "password_reset_url": url_safe_string,
                                          "created_at": datetime.now(timezone.utc)})

    # TODO: Mkae this look better
    send_email(receiver_email=email, subject="Password Reset Requested",
               body=f"Please click the following link to reset your password: {settings.FRONTEND_URL}/auth/reset-password?reset_token={url_safe_string}")


async def verify_email_helper(email: str):
    # Generate a random URL-safe string and store it in MongoDB
    random_bytes = secrets.token_bytes(64)
    url_safe_string = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    await email_verification_coll.insert_one({"email": email, "email_verification_url": url_safe_string,
                                          "created_at": datetime.now(timezone.utc)})

    # TODO: Make this look better
    send_email(receiver_email=email, subject="Verify Your Email Address",
               body=f"Please click the following link to verify your email address: {settings.FRONTEND_URL}/auth/verify-email?email_verification_token={url_safe_string}")
