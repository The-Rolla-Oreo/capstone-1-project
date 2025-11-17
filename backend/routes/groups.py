from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Form, Response
from pymongo import AsyncMongoClient

from bson.objectid import ObjectId
from datetime import datetime, timezone

from backend.settings import get_settings
from backend.models import User
from backend.helpers.helper_auth import get_current_user
from backend.helpers.helper_groups import add_groups_to_user
from .auth import read_users_me



settings = get_settings()



# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION
GROUPS_COLLECTION = settings.GROUPS_COLLECTION
PASSWORD_RESET_COLLECTION = settings.PASSWORD_RESET_COLLECTION

# Initialize MongoDB client
client = AsyncMongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]
groups_coll = _db[GROUPS_COLLECTION]
password_reset_coll = _db[PASSWORD_RESET_COLLECTION]


router = APIRouter()



@router.post("/create-group")
async def create_houshold_group(
    group_name: Annotated[str, Form(..., min_length=5, max_length=35)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Description
    -----------
    - Creates and adds document with group 
      information to Groups collection

    - Adds the newly created group id to the
      group admin's DB record 
    
    Returns
    -------
    None

    """

    # Get current user (i.e. user making group / group_admin) info
    group_admin_id = current_user.id
    group_admin_username = current_user.username

    # Create a new group id
    new_group_id = ObjectId()

    # Document to insert
    groups_doc = {
        "_id": new_group_id,
        "group_name": group_name,
        "group_admin_id": ObjectId(group_admin_id),
        "group_admin_username": group_admin_username,
        "users_in_group": [ObjectId(group_admin_id)],
        "created_at": datetime.now(timezone.utc)
    }

    # Update group admin's db record
    await add_groups_to_user(ObjectId(group_admin_id), [new_group_id])

    # Insert into group doc in MongoDB
    await groups_coll.insert_one(groups_doc)


    return {"msg": "Group created successfully"}    
