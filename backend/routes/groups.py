from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Form
from pymongo import AsyncMongoClient

from bson.objectid import ObjectId
from datetime import datetime, timezone

from backend.settings import get_settings
from backend.models import User
from backend.helpers.helper_auth import get_current_user
from backend.helpers.helper_groups import add_groups_to_user, invite_user_to_group



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
group_invites_coll = _db[GROUP_INVITES_COLLECTION]
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

    # Prevent creating a group if user already belongs to any group
    admin_obj_id = ObjectId(group_admin_id)

    admin_doc = await users_coll.find_one({"_id": admin_obj_id})
    if admin_doc:
        existing_group_ids = admin_doc.get("group_ids")
        if existing_group_ids and len(existing_group_ids) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already belongs to a group and cannot create a new one.",
            )


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



@router.post("/invite-user")
async def invite_user(email: Annotated[str, Form(..., regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")],
                      current_user: Annotated[User, Depends(get_current_user)],
                      background_tasks: BackgroundTasks,
    ):
    """
    Description
    -----------
    - Get id of group that current user belongs to
    - Makes sure invitee with given email exists
    - Makes sure current user hasn't sent an invite to this user already
    - Run the invite user to group functionality (sends an email to invitee)
    
    Returns
    -------
    None    

    """
   
    # Get current users group_ids list
    group_ids = current_user.group_ids
    
    # If user doesn't belong to group, cannot invite people
    if not group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot invite user. You are not part of a group."
        )
    else:
        current_user_group_id = ObjectId(group_ids[0])

    # Make sure the invitee user exists
    invitee_user = await users_coll.find_one({"email": email})
    if not invitee_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist with that email"
        )
    
    # Make sure the user has not already sent an invite to this specific email
    already_requested = await group_invites_coll.find_one({
        "email": email,
        "group_id": current_user_group_id
    })
    if already_requested:
        return {"msg": "Invite link already sent to this email."}

    # Query for the groups doc
    group_doc = await groups_coll.find_one({"_id": current_user_group_id})
    group_name = group_doc["group_name"]

    # Have invite user functionality run as background task
    background_tasks.add_task(invite_user_to_group, email, current_user_group_id, group_name)

    return {"msg": "Invite link sent to user's email if an account with that email exists."}



@router.post("/join-group")
async def join_houshold_group(
    current_user: Annotated[User, Depends(get_current_user)],
    invite_token: str = Form()
) -> None:
    """
    Description
    -----------
    - Check if current user is already in a group. If yes, cannot join
    - Checks if invite token is valid
    - Finds group_id that invite token corresponds to
    - Adds current user to the group doc
    - Adds group_id to the current user's group_ids
    - Deletes the group invite doc
    
    Returns
    -------
    None

    """

    # Resolve current user ObjectId and check user's existing groups
    current_user_id = ObjectId(current_user.id)
    user_doc = await users_coll.find_one({"_id": current_user_id})
    existing_group_ids = user_doc.get("group_ids") if user_doc else []

    # If current user is already in a group they cannot join another one.
    if existing_group_ids and len(existing_group_ids) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already belongs to a group and cannot join another one.",
        )
    
    # Get the group invite doc to check if invite token is valid
    # we search by email AND invite token to ensure current user
    # is the correct invitee with matching email
    group_invites_doc = await group_invites_coll.find_one(
        {"email": user_doc.get("email"),
         "invite_token": invite_token}
    )
    # Check if the invite token is valid
    if not group_invites_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group invite token",
        )

    # Get group id from the group invite doc
    group_id = group_invites_doc.get("group_id")

    # Add the current user to the group
    await groups_coll.update_one(
        {"_id": group_id},
        {"$addToSet": {"users_in_group": current_user_id}}  # Add user to group
    )
    
    # Update the user's document to include the group ID
    await users_coll.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$addToSet": {"group_ids": group_id}}  # Add group ID to user's group_ids
    )

    # Delete the group invite doc after successful joining
    await group_invites_coll.delete_one({"invite_token": invite_token})

    return {"msg": "Successfully joined the group."}



@router.post("/leave-group")
async def leave_household_group(
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Description
    -----------
    - Removes the current user from their first group (group_ids[0])
    - Removes the user from the group's users_in_group array
    - Deletes the group if it becomes empty
    - Promotes first remaining user as admin if current user was admin

    Returns
    -------
    None

    """
    # resolve user/object ids
    user_obj_id = ObjectId(current_user.id)

    # fetch user document and ensure they belong to a group
    user_doc = await users_coll.find_one({"_id": user_obj_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    group_ids = user_doc.get("group_ids") or []
    if not group_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to any group.",
        )

    # assume we remove the first group id (group_ids[0])
    target_group_id = group_ids[0]
    # ensure we have an ObjectId value
    if not isinstance(target_group_id, ObjectId):
        target_group_id = ObjectId(target_group_id)

    # remove the group id from the user's group_ids array
    # $pull to removes specific id (safe even if it's not first)
    await users_coll.update_one(
        {"_id": user_obj_id},
        {"$pull": {"group_ids": target_group_id}},
    )

    # remove the user from the group's users_in_group array
    await groups_coll.update_one(
        {"_id": target_group_id},
        {"$pull": {"users_in_group": user_obj_id}},
    )

    # if the group is now empty, deletes it
    # otherwise, if current user was admin makes another user admin
    group_doc = await groups_coll.find_one({"_id": target_group_id})
    if group_doc:
        users_in_group = group_doc.get("users_in_group", [])
        if not users_in_group:
            # delete empty group
            await groups_coll.delete_one({"_id": target_group_id})
        else:
            # if the user was the admin, you may want to promote another member
            if group_doc.get("group_admin_id") == user_obj_id:
                # promote first remaining member to admin
                new_admin = users_in_group[0]
                new_admin_doc = await users_coll.find_one({"_id": new_admin})
                new_admin_username = new_admin_doc.get("username")
                await groups_coll.update_one(
                    {"_id": target_group_id},
                    {"$set": {"group_admin_id": new_admin, "group_admin_username": new_admin_username}}
                )

    return {"msg": "Left group successfully."}

    
    