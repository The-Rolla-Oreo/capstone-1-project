from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Form, Response
from fastapi.security import OAuth2PasswordRequestForm
from backend.models import User
from motor.motor_asyncio import AsyncIOMotorClient

from backend.settings import get_settings

from backend.helpers.helper_auth import get_password_hash, authenticate_user, create_access_token, get_current_user


settings = get_settings()

# JWT config
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]


router = APIRouter()


@router.post("/register", status_code=201)
async def register_user(
    username: Annotated[str, Form(..., min_length=5, max_length=35)],
    password: Annotated[str, Form(..., min_length=15)],
    email: Annotated[str, Form(..., regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")],
    full_name: Annotated[str, Form(..., min_length=5, max_length=100)],
):
    """
    - Checks that the username does not already exist.
    - Hashes the password
    - Stores the user document in MongoDB.
    """
    # Make sure username is unique
    existing_username = await users_coll.find_one({"username": username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Make sure email is unique
    existing_email = await users_coll.find_one({"email": email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already taken",
        )

    # Hash the password
    hashed_pwd = get_password_hash(password)

    # Document to insert
    user_doc = {
        "username": username,
        "full_name": full_name,
        "email": email,
        "hashed_password": hashed_pwd,
    }

    # Insert into MongoDB
    await users_coll.insert_one(user_doc)

    return {"msg": "User registered successfully"}


@router.post("/login")
async def login_for_access_token(
    response: Response, # Needed to set cookie
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], # Makes endpoint take data in OAuth2PasswordRequestForm format
):

    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta_in_min=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # TODO: Set cookie parameters dynamically depending on dev vs prod env
    # Set JWT as HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, # Convert minutes to seconds
        path="/",
    )

    return {"msg": "Login successful"}


@router.get("/my-details", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.post("/logout")
async def logout(response: Response):
    """Delete the auth cookie to log out the user."""
    response.delete_cookie(key="access_token", path="/")
    return Response(status_code=204)
