import secrets
from datetime import datetime, timezone

from backend.settings import get_settings
from backend.helpers.helper_email import send_email

from pymongo import AsyncMongoClient
from bson.objectid import ObjectId



settings = get_settings()



# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION
GROUPS_COLLECTION = settings.GROUPS_COLLECTION
PASSWORD_RESET_COLLECTION = settings.PASSWORD_RESET_COLLECTION
GROUP_INVITES_COLLECTION = settings.GROUP_INVITES_COLLECTION

# Initialize MongoDB client
client = AsyncMongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]
groups_coll = _db[GROUPS_COLLECTION]
password_reset_coll = _db[PASSWORD_RESET_COLLECTION]
group_invites_coll = _db[GROUP_INVITES_COLLECTION]

async def add_groups_to_user(user_id: ObjectId, group_id_list: list[ObjectId]) -> None:
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

    # NOTE: `$addToSet` adds the value only if it does not already exist in the array
    await users_coll.update_one(
        {"_id": user_id}, 
        {"$addToSet": {"group_ids": {"$each": group_id_list}}}
    )



async def invite_user_to_group(email: str, group_id: ObjectId, group_name: str):

    # Generate a cleaner URL-safe token
    # secrets.token_urlsafe(32) gives you a random string approx 43 chars long
    invite_token = secrets.token_urlsafe(32)    

    await group_invites_coll.insert_one({
        "email": email, 
        "group_id": group_id,
        "group_name": group_name,
        "invite_token": invite_token,
        "created_at": datetime.now(timezone.utc)
    })

    # TODO: Mkae this look better
    send_email(receiver_email=email, subject=f"Invite Link To Join Group [{group_name}]",
               body=f"Please click the following link to reset your password: {settings.FRONTEND_URL}/groups/join-group?invite_token={invite_token}")