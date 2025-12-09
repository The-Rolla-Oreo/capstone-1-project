from bson.objectid import ObjectId
import datetime
from dateutil.rrule import rrulestr
from dateutil.parser import parse
from fastapi import HTTPException, status
from pymongo import AsyncMongoClient

from backend.settings import get_settings

settings = get_settings()

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION

# Initialize MongoDB client
client = AsyncMongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]


async def validate_and_get_user_ids(usernames: list[str], group_id: ObjectId) -> list[ObjectId]:
    """
    Validates a list of usernames to ensure they exist and belong to the specified group.
    
    Parameters:
    - `usernames`: A list of usernames to validate.
    - `group_id`: The ObjectId of the group the users must belong to.

    Returns:
    - A list of ObjectIds corresponding to the validated usernames.
    
    Raises:
    - `HTTPException(400, ...)`: If a user is not found or not in the group.
    """
    user_obj_ids = []
    for username in usernames:
        user_doc = await users_coll.find_one({"username": username})
        if not user_doc or not user_doc.get("group_ids") or user_doc["group_ids"][0] != group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with username '{username}' not found or not in the same group.",
            )
        user_obj_ids.append(user_doc["_id"])
    return user_obj_ids

def recalculate_schedule(rrule_str: str | None, start_date_str: str | None, existing_chore: dict) -> dict:
    """
    Recalculates the recurring chore's schedule if the rrule or start date has changed.
    
    Parameters:
    - `rrule_str`: The new recurrence rule string, if provided.
    - `start_date_str`: The new start date string, if provided.
    - `existing_chore`: The existing recurring chore document from the database.

    Returns:
    - A dictionary containing the updated schedule fields (`rrule`, `start_date`, `next_due_date`).
      Returns an empty dictionary if no schedule fields were updated.
    
    Raises:
    - `HTTPException(400, ...)`: If the new rrule or start date is invalid.
    """
    if rrule_str is None and start_date_str is None:
        return {}

    new_rrule_str = rrule_str if rrule_str is not None else existing_chore["rrule"]
    new_start_date_str = start_date_str if start_date_str is not None else existing_chore["start_date"].isoformat()
    
    try:
        start_date = parse(new_start_date_str)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=datetime.timezone.utc)
        
        rule = rrulestr(new_rrule_str, dtstart=start_date)

        yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        next_due_date = rule.after(yesterday)

        if next_due_date is None:
            raise ValueError("Could not determine next due date for the given rule.")

        return {
            "rrule": new_rrule_str,
            "start_date": start_date,
            "next_due_date": next_due_date,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rrule or start_date: {e}",
        )
