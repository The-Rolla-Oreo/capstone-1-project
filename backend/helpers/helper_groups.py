from backend.models import UserInDB, TokenData
from backend.settings import get_settings
from pymongo import AsyncMongoClient
from bson.objectid import ObjectId


settings = get_settings()



# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION
PASSWORD_RESET_COLLECTION = settings.PASSWORD_RESET_COLLECTION

# Initialize MongoDB client
client = AsyncMongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]
password_reset_coll = _db[PASSWORD_RESET_COLLECTION]

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


