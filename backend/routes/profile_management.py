import io
from typing import Annotated

import boto3
from PIL import Image
from botocore.client import Config
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, BackgroundTasks

from backend.helpers.helper_auth import get_current_user
from backend.helpers.helper_email import send_email
from backend.models import User
from pymongo import AsyncMongoClient

from backend.settings import get_settings


settings = get_settings()

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION

# S3 config
S3_ENDPOINT = settings.S3_ENDPOINT
S3_ACCESS_KEY = settings.S3_ACCESS_KEY
S3_SECRET_KEY = settings.S3_SECRET_KEY
S3_BUCKET_NAME = settings.S3_BUCKET_NAME

# Initialize MongoDB client
client = AsyncMongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(s3={"addressing_style": "path"}),
)

router = APIRouter()

ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]
PFP_SIZE = (256, 256)


async def upload_pfp_bg(user: User, pfp: UploadFile):
    # Read the image data into memory
    image_data = await pfp.read()

    # Open the image with Pillow
    try:
        image = Image.open(io.BytesIO(image_data))
    except Exception:
        send_email(
            receiver_email=user.email,
            subject="Profile Picture Upload Failed",
            body="We could not read the uploaded image file. Please try again with a different file.",
        )
        return

    # Resize the image
    image.thumbnail(PFP_SIZE)

    # Save the resized image to an in-memory buffer
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Define the S3 object name
    s3_object_name = f"profile_pictures/{user.id}.png"

    # Upload the image to S3
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_object_name,
            Body=buffer,
            ContentType="image/png",
            ACL="public-read",
        )
    except Exception:
        send_email(
            receiver_email=user.email,
            subject="Profile Picture Upload Failed",
            body="We could not upload your new profile picture to our storage. Please try again later.",
        )
        return

    # Get the URL of the uploaded object
    s3_url = f"{S3_ENDPOINT}/{S3_BUCKET_NAME}/{s3_object_name}"

    # Update the user's document in MongoDB with the S3 URL
    await users_coll.update_one(
        {"username": user.username}, {"$set": {"profile_picture_url": s3_url}}
    )


@router.post("/set-profile-picture")
async def set_profile_pic(
    current_user: Annotated[User, Depends(get_current_user)],
    pfp: UploadFile,
    background_tasks: BackgroundTasks,
):
    """
    - Accepts an image
    - Resizes it to 250 x 250 pixels
    - Stores it in S3 bucket and sets it as public
    - Adds the S3 URL to the user's document in MongoDB
    """
    # Check if the uploaded file is an image
    if pfp.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File of type {pfp.content_type} is not supported. Please upload a JPEG or PNG.",
        )

    # TODO: Use celery for background tasks once GH PR #16 is merged
    background_tasks.add_task(upload_pfp_bg, current_user, pfp)

    return {"msg": "Profile picture upload in progress."}
