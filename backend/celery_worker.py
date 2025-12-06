import base64
import secrets
from datetime import datetime, timezone

from .celery_app import celery_app
from .helpers.helper_email import send_email
from .settings import get_settings
from pymongo import MongoClient

from bson.objectid import ObjectId

settings = get_settings()

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION
PASSWORD_RESET_COLLECTION = settings.PASSWORD_RESET_COLLECTION
EMAIL_VERIFICATION_COLLECTION = settings.EMAIL_VERIFICATION_COLLECTION
GROUPS_COLLECTION = settings.GROUPS_COLLECTION
GROUP_INVITES_COLLECTION = settings.GROUP_INVITES_COLLECTION

# Initialize MongoDB client
# Note: Celery workers should use a synchronous MongoDB client
client = MongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]
password_reset_coll = _db[PASSWORD_RESET_COLLECTION]
email_verification_coll = _db[EMAIL_VERIFICATION_COLLECTION]
groups_coll = _db[GROUPS_COLLECTION]
group_invites_coll = _db[GROUP_INVITES_COLLECTION]

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


@celery_app.task
def add_groups_to_user(user_id: str, group_id_list: list[str]) -> None:
    """
    Description
    -----------
    Adds group ids to a user's DB record

    Precondition
    ------------
    User must exist

    Returns
    -------
    None
    """

    # Convert to BSON object ids
    user_bson_id = ObjectId(user_id)
    group_bson_id_list = [ObjectId(group_id_str) for group_id_str in group_id_list]

    # NOTE: `$addToSet` adds the value only if it does not already exist in the array
    users_coll.update_one(
        {"_id": user_bson_id}, 
        {"$addToSet": {"group_ids": {"$each": group_bson_id_list}}}
    )



@celery_app.task
def invite_user_to_group(email: str, group_id: str, group_name: str):
    """
    Description
    -----------
    - Generated invite token
    - Inserts group invite doc into database
    - Calls Celery task function to send invite email
    """
    
    # Generate a cleaner URL-safe token
    # secrets.token_urlsafe(32) gives you a random string approx 43 chars long
    invite_token = secrets.token_urlsafe(32)   

    group_bson_id = ObjectId(group_id) 

    group_invites_coll.insert_one({
        "email": email, 
        "group_id": group_bson_id,
        "group_name": group_name,
        "invite_token": invite_token,
        "created_at": datetime.now(timezone.utc)
    })

    send_email(receiver_email=email, 
               subject=f"Invite Link To Join Group [{group_name}]",
               body=f"Please click the following link to reset your password: {settings.FRONTEND_URL}/groups/join-group?invite_token={invite_token}"
    ) 


