import base64
import io
import secrets
from datetime import datetime, timezone

import boto3
from PIL import Image
from botocore.client import Config

from .celery_app import celery_app
from .helpers.helper_email import send_email
from .models import User
from .settings import get_settings
from pymongo import MongoClient

settings = get_settings()

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION
PASSWORD_RESET_COLLECTION = settings.PASSWORD_RESET_COLLECTION
EMAIL_VERIFICATION_COLLECTION = settings.EMAIL_VERIFICATION_COLLECTION

# S3 config
S3_ENDPOINT = settings.S3_ENDPOINT
S3_ACCESS_KEY = settings.S3_ACCESS_KEY
S3_SECRET_KEY = settings.S3_SECRET_KEY
S3_BUCKET_NAME = settings.S3_BUCKET_NAME
PFP_SIZE = (256, 256)


# Initialize MongoDB client
# Note: Celery workers should use a synchronous MongoDB client
client = MongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]
password_reset_coll = _db[PASSWORD_RESET_COLLECTION]
email_verification_coll = _db[EMAIL_VERIFICATION_COLLECTION]

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(s3={"addressing_style": "path"}),
)


@celery_app.task
def upload_pfp_task(user_dict: dict, pfp_data: bytes):
    # Recreate the user object
    user = User(**user_dict)

    # Open the image with Pillow
    try:
        image = Image.open(io.BytesIO(pfp_data))
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
    users_coll.update_one(
        {"username": user.username}, {"$set": {"profile_picture_url": s3_url}}
    )


@celery_app.task
def forgot_password_requested_task(email: str):
    # Note: We don't let user know if email exists so we can prevent account enumeration attacks

    # Make sure the user exists
    user_exists = users_coll.find_one({"email": email})
    if not user_exists:
        return

    # Make sure the user has not already requested a password reset
    already_requested = password_reset_coll.find_one({"email": email})
    if already_requested:
        return

    # Generate a random URL-safe string and store it in MongoDB
    random_bytes = secrets.token_bytes(64)
    url_safe_string = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    password_reset_coll.insert_one({"email": email, "password_reset_url": url_safe_string,
                                          "created_at": datetime.now(timezone.utc)})

    # TODO: Mkae this look better
    send_email(receiver_email=email, subject="Password Reset Requested",
               body=f"Please click the following link to reset your password: {settings.FRONTEND_URL}/auth/reset-password?reset_token={url_safe_string}")


@celery_app.task
def verify_email_helper_task(email: str):
    # Generate a random URL-safe string and store it in MongoDB
    random_bytes = secrets.token_bytes(64)
    url_safe_string = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    email_verification_coll.insert_one({"email": email, "email_verification_url": url_safe_string,
                                          "created_at": datetime.now(timezone.utc)})

    # TODO: Make this look better
    send_email(receiver_email=email, subject="Verify Your Email Address",
               body=f"Please click the following link to verify your email address: {settings.FRONTEND_URL}/auth/verify-email?email_verification_token={url_safe_string}")
