import base64
import secrets
from datetime import datetime, timezone

from .celery_app import celery_app
from .helpers.helper_email import send_email
from .settings import get_settings
from pymongo import MongoClient

settings = get_settings()

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION
PASSWORD_RESET_COLLECTION = settings.PASSWORD_RESET_COLLECTION
EMAIL_VERIFICATION_COLLECTION = settings.EMAIL_VERIFICATION_COLLECTION

# Initialize MongoDB client
# Note: Celery workers should use a synchronous MongoDB client
client = MongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]
password_reset_coll = _db[PASSWORD_RESET_COLLECTION]
email_verification_coll = _db[EMAIL_VERIFICATION_COLLECTION]


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
