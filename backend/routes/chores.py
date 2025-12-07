from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Form
from pymongo import AsyncMongoClient

from dateutil.rrule import rrulestr
from dateutil.parser import parse

from bson.objectid import ObjectId
import datetime

from backend.settings import get_settings
from backend.models import User, Chore, RecurringChore
from backend.helpers.helper_auth import get_current_user


settings = get_settings()

# MongoDB config
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.DB_NAME
USERS_COLLECTION = settings.USERS_COLLECTION
GROUPS_COLLECTION = settings.GROUPS_COLLECTION
CHORES_COLLECTION = settings.CHORES_COLLECTION
RECURRING_CHORES_COLLECTION = settings.RECURRING_CHORES_COLLECTION

# Initialize MongoDB client
# We use an asynchronous client here because FastAPI is an async framework.
# This allows the server to handle other requests while waiting for database operations to complete.
client = AsyncMongoClient(MONGO_URI)
_db = client[DB_NAME]
users_coll = _db[USERS_COLLECTION]
groups_coll = _db[GROUPS_COLLECTION]
chores_coll = _db[CHORES_COLLECTION]
recurring_chores_coll = _db[RECURRING_CHORES_COLLECTION]


router = APIRouter()


@router.post("/create-chore")
async def create_chore(
    current_user: Annotated[User, Depends(get_current_user)],
    chore_name: str = Form(...),
    chore_description: str = Form(...),
    assigned_username: str | None = Form(None),
    recurring_chore_id: str | None = Form(None),
) -> dict:
    """
    Creates a new chore. This can be a standalone chore or one linked to a recurring chore schedule.

    A chore is a single task that can be assigned to a user in a group. It can be created manually
    or be generated automatically from a recurring chore schedule.

    Parameters:
    - `current_user`: The authenticated user creating the chore (injected by dependency).
    - `chore_name`: The name of the chore.
    - `chore_description`: A detailed description of the chore.
    - `assigned_username`: Optional. The username of the user to whom this chore is assigned.
                         If not provided, the chore is assigned to the current user.
    - `recurring_chore_id`: Optional. The ID of the recurring chore schedule this chore originated from.
                           This is used to link a generated chore back to its schedule.

    Returns:
    - A dictionary containing a success message and the ID of the newly created chore.

    Raises:
    - `HTTPException(403, "You must be in a group to create a chore.")`: If the current user is not part of any group.
    - `HTTPException(400, "User with username '{username}' not found.")`: If the specified `assigned_username` does not exist.
    - `HTTPException(400, "Assigned user is not in the same group.")`: If the assigned user is not in the same group as the current user.
    """
    # A user must be part of a group to create a chore, as chores are group-based.
    if not current_user.group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be in a group to create a chore.",
        )
    
    # If no username is provided for assignment, the chore is assigned to the user creating it.
    if assigned_username is None or assigned_username == "":
        assigned_user_obj_id = ObjectId(current_user.id)
        # We still need to fetch the user document to verify group membership.
        assigned_user_doc = await users_coll.find_one({"_id": assigned_user_obj_id})
    else:
        # If a username is provided, find the corresponding user in the database.
        assigned_user_doc = await users_coll.find_one({"username": assigned_username})
        if not assigned_user_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with username '{assigned_username}' not found.",
            )
        assigned_user_obj_id = assigned_user_doc["_id"]
    
    # Chores are scoped to a single group. For simplicity, we use the user's first group.
    group_id = ObjectId(current_user.group_ids[0])

    # It's crucial to ensure that the assigned user belongs to the same group as the creator.
    # This prevents cross-group chore assignments.
    if not assigned_user_doc.get("group_ids") or assigned_user_doc["group_ids"][0] != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user is not in the same group.",
        )
    
    # Construct the chore document to be inserted into the database.
    chore_doc = {
        "group_id": group_id,
        "chore_name": chore_name,
        "chore_description": chore_description,
        "assigned_user_id": assigned_user_obj_id,
        "is_completed": False,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "completed_at": None,
    }
    # If the chore is generated from a recurring schedule, link it back.
    if recurring_chore_id:
        chore_doc["recurring_chore_id"] = ObjectId(recurring_chore_id)

    # Insert the new chore document into the database.
    result = await chores_coll.insert_one(chore_doc)
    
    return {"message": "Chore created successfully", "chore_id": str(result.inserted_id)}


@router.get("/chores")
async def get_chores(current_user: Annotated[User, Depends(get_current_user)]) -> list[Chore]:
    """
    Retrieves all chores for the current user's primary group.

    This endpoint fetches all chore documents associated with the user's group, allowing
    the frontend to display a list of all chores, their assignees, and their completion status.

    Parameters:
    - `current_user`: The authenticated user (injected by dependency).

    Returns:
    - A list of `Chore` objects, where each object represents a chore in the group.

    Raises:
    - `HTTPException(403, "You must be in a group to view chores.")`: If the current user is not part of any group.
    """
    # Viewing chores is a group activity. A user must be in a group.
    if not current_user.group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be in a group to view chores.",
        )

    # As with chore creation, we operate on the user's first group.
    group_id = ObjectId(current_user.group_ids[0])

    # Retrieve all chores that belong to the user's group.
    chores_cursor = chores_coll.find({"group_id": group_id})
    # Convert the async cursor to a list of documents.
    chores_list = await chores_cursor.to_list(length=None)

    # The Pydantic models expect string representations of ObjectIds for JSON serialization.
    # We loop through the list and convert all ObjectId fields to strings.
    for chore in chores_list:
        chore["_id"] = str(chore["_id"])
        chore["assigned_user_id"] = str(chore["assigned_user_id"])
        # Not all chores are from a recurring schedule, so we must check for existence.
        if "recurring_chore_id" in chore and chore["recurring_chore_id"] is not None:
            chore["recurring_chore_id"] = str(chore["recurring_chore_id"])

    return chores_list


@router.post("/complete-chore/{chore_id}")
async def complete_chore(
    chore_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Marks a specific chore as completed.

    This is a key action in the application's workflow. When a user completes a chore,
    they can mark it as such, which updates its status in the database.

    Parameters:
    - `chore_id`: The ID of the chore to mark as complete.
    - `current_user`: The authenticated user performing the action (injected by dependency).

    Returns:
    - A dictionary containing a success message.

    Raises:
    - `HTTPException(403, "You must be in a group to complete a chore.")`: If the user is not in a group.
    - `HTTPException(404, "Chore not found in your group.")`: If the chore ID is invalid or the chore
      does not belong to the user's group.
    - `HTTPException(500, "Failed to update chore.")`: If the database operation fails.
    """
    if not current_user.group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be in a group to complete a chore.",
        )

    group_id = ObjectId(current_user.group_ids[0])
    chore_obj_id = ObjectId(chore_id)

    # First, we must verify that the chore exists and belongs to the user's group.
    # This prevents users from completing chores in other groups.
    chore = await chores_coll.find_one({"_id": chore_obj_id, "group_id": group_id})
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found in your group.",
        )

    # Update the chore document by setting `is_completed` to True and recording the completion time.
    result = await chores_coll.update_one(
        {"_id": chore_obj_id},
        {"$set": {"is_completed": True, "completed_at": datetime.datetime.now(datetime.timezone.utc)}},
    )

    if result.modified_count == 1:
        return {"message": "Chore marked as complete."}
    else:
        # This can happen if the chore was already completed or if there was a database issue.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chore.",
        )


@router.delete("/delete-chore/{chore_id}")
async def delete_chore(
    chore_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Deletes a specific chore.

    This provides a way to remove chores that were created by mistake or are no longer needed.

    Parameters:
    - `chore_id`: The ID of the chore to delete.
    - `current_user`: The authenticated user performing the action.

    Returns:
    - A dictionary containing a success message.

    Raises:
    - `HTTPException(403, "You must be in a group to delete a chore.")`: If the user is not in a group.
    - `HTTPException(404, "Chore not found in your group.")`: If the chore ID is invalid or not in the user's group.
    - `HTTPException(500, "Failed to delete chore.")`: If the database operation fails.
    """
    if not current_user.group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be in a group to delete a chore.",
        )

    group_id = ObjectId(current_user.group_ids[0])
    chore_obj_id = ObjectId(chore_id)

    # As with completing a chore, we verify ownership before deleting.
    chore = await chores_coll.find_one({"_id": chore_obj_id, "group_id": group_id})
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found in your group.",
        )

    # Perform the delete operation.
    result = await chores_coll.delete_one({"_id": chore_obj_id})

    if result.deleted_count == 1:
        return {"message": "Chore deleted successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chore.",
        )


@router.post("/recurring-chores/")
async def create_recurring_chore(
    current_user: Annotated[User, Depends(get_current_user)],
    chore_name: str = Form(...),
    chore_description: str = Form(...),
    assigned_usernames: list[str] = Form(...),
    rrule_str: str = Form(...),
    start_date_str: str = Form(...),
) -> dict:
    """
    Creates a new recurring chore schedule.

    This is the core of the chore automation feature. A recurring chore schedule defines a chore
    that repeats over time (e.g., "Take out the trash every Tuesday"). The system then uses this
    schedule to automatically generate individual chore documents when they are due.

    Parameters:
    - `current_user`: The authenticated user creating the schedule.
    - `chore_name`: The name of the recurring chore.
    - `chore_description`: The description of the recurring chore.
    - `assigned_usernames`: A list of usernames who will be assigned this chore in rotation.
    - `rrule_str`: The iCalendar RRULE string that defines the recurrence pattern (e.g., "FREQ=WEEKLY;BYDAY=TU").
    - `start_date_str`: The date the recurrence should start, in a parseable string format (e.g., "2025-12-01T10:00:00Z").

    Returns:
    - A dictionary containing a success message and the ID of the new recurring chore schedule.

    Raises:
    - `HTTPException(403, ...)`: If the user is not in a group.
    - `HTTPException(400, ...)`: If any assigned users are not found or are not in the same group.
    - `HTTPException(400, ...)`: If the `rrule_str` or `start_date_str` is invalid.
    """
    if not current_user.group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be in a group to create a recurring chore.",
        )
    
    group_id = ObjectId(current_user.group_ids[0])

    # Validate that all assigned users exist and belong to the same group.
    # This prevents assigning chores to users who can't see them.
    assigned_user_obj_ids = []
    for username in assigned_usernames:
        user_doc = await users_coll.find_one({"username": username})
        if not user_doc or not user_doc.get("group_ids") or user_doc["group_ids"][0] != group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with username '{username}' not found or not in the same group.",
            )
        assigned_user_obj_ids.append(user_doc["_id"])

    # Parse the recurrence rule and calculate the first due date.
    try:
        # The start date from the client might not have timezone info.
        # We parse it and then ensure it's timezone-aware by setting it to UTC if it's naive.
        # This prevents "can't compare offset-naive and offset-aware datetimes" errors.
        start_date = parse(start_date_str)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=datetime.timezone.utc)
        
        rule = rrulestr(rrule_str, dtstart=start_date)

        # To calculate the initial `next_due_date`, we find the first occurrence of the rule
        # that is on or after the start date. A simple way to do this is to ask for the first
        # occurrence after yesterday.
        yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        next_due_date = rule.after(yesterday)

        # If `rule.after()` returns None, it means no future occurrences could be found,
        # which indicates a problem with the rule (e.g., a finite rule that has already ended).
        if next_due_date is None:
            raise ValueError("Could not determine next due date for the given rule.")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rrule or start_date: {e}",
        )

    # Create the document for the recurring chore schedule.
    recurring_chore_doc = {
        "group_id": group_id,
        "chore_name": chore_name,
        "chore_description": chore_description,
        "assigned_user_ids": assigned_user_obj_ids,
        "rrule": rrule_str,
        "start_date": start_date,
        "next_due_date": next_due_date,
        "is_active": True,  # Schedules are active by default.
        "last_assigned_user_index": 0,  # Initialize the rotation index.
        "created_at": datetime.datetime.now(datetime.timezone.utc),
    }

    result = await recurring_chores_coll.insert_one(recurring_chore_doc)

    return {"message": "Recurring chore created successfully", "recurring_chore_id": str(result.inserted_id)}

@router.get("/recurring-chores/")
async def get_recurring_chores(current_user: Annotated[User, Depends(get_current_user)]) -> list[RecurringChore]:
    """
    Retrieves all recurring chore schedules for the current user's group.

    Parameters:
    - `current_user`: The authenticated user.

    Returns:
    - A list of `RecurringChore` objects.

    Raises:
    - `HTTPException(403, ...)`: If the user is not in a group.
    """
    if not current_user.group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be in a group to view recurring chores.",
        )

    group_id = ObjectId(current_user.group_ids[0])

    # Find all recurring chore schedules associated with the user's group.
    recurring_chores_cursor = recurring_chores_coll.find({"group_id": group_id})
    recurring_chores_list = await recurring_chores_cursor.to_list(length=None)

    # Convert ObjectIds to strings for JSON compatibility.
    for chore in recurring_chores_list:
        chore["_id"] = str(chore["_id"])
        chore["group_id"] = str(chore["group_id"])
        chore["assigned_user_ids"] = [str(uid) for uid in chore["assigned_user_ids"]]

    return recurring_chores_list

@router.put("/recurring-chores/{recurring_chore_id}")
async def update_recurring_chore(
    recurring_chore_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    chore_name: str = Form(None),
    chore_description: str = Form(None),
    assigned_usernames: list[str] = Form(None),
    rrule_str: str = Form(None),
    start_date_str: str = Form(None),
    is_active: bool = Form(None),
) -> dict:
    """
    Updates an existing recurring chore schedule. Allows for partial updates of fields.

    This endpoint is flexible, allowing a user to change any part of the recurring chore's
    definition, such as its name, the rotation of users, or the recurrence rule itself.

    Parameters:
    - `recurring_chore_id`: The ID of the recurring chore to update.
    - `current_user`: The authenticated user.
    - `chore_name`: Optional. The new name for the recurring chore.
    - `chore_description`: Optional. The new description.
    - `assigned_usernames`: Optional. A new list of usernames for the rotation.
    - `rrule_str`: Optional. A new iCalendar RRULE string.
    - `start_date_str`: Optional. A new start date for the recurrence.
    - `is_active`: Optional. Boolean to activate or deactivate the schedule.

    Returns:
    - A dictionary containing a success message.

    Raises:
    - `HTTPException(403, ...)`: If the user is not in a group.
    - `HTTPException(404, ...)`: If the recurring chore is not found in the user's group.
    - `HTTPException(400, ...)`: If any provided usernames are invalid.
    - `HTTPException(400, ...)`: If the `rrule_str` or `start_date_str` is invalid.
    - `HTTPException(400, "No fields to update.")`: If no update parameters are provided.
    - `HTTPException(500, "Failed to update recurring chore.")`: If the database update fails.
    """
    if not current_user.group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be in a group to update a recurring chore.",
        )

    group_id = ObjectId(current_user.group_ids[0])
    recurring_chore_obj_id = ObjectId(recurring_chore_id)

    # Verify that the recurring chore exists and belongs to the user's group.
    existing_chore = await recurring_chores_coll.find_one({"_id": recurring_chore_obj_id, "group_id": group_id})
    if not existing_chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring chore not found in your group.",
        )

    # Build a dictionary of fields to update. This allows for partial updates.
    update_doc = {}
    if chore_name is not None:
        update_doc["chore_name"] = chore_name
    if chore_description is not None:
        update_doc["chore_description"] = chore_description
    if is_active is not None:
        update_doc["is_active"] = is_active
    
    # If a new list of usernames is provided, validate them.
    if assigned_usernames is not None:
        assigned_user_obj_ids = []
        for username in assigned_usernames:
            user_doc = await users_coll.find_one({"username": username})
            if not user_doc or not user_doc.get("group_ids") or user_doc["group_ids"][0] != group_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with username '{username}' not found or not in the same group.",
                )
            assigned_user_obj_ids.append(user_doc["_id"])
        update_doc["assigned_user_ids"] = assigned_user_obj_ids

    # If the schedule changes, we need to recalculate the `next_due_date`.
    if rrule_str is not None or start_date_str is not None:
        # Use the new value if provided, otherwise fall back to the existing value.
        new_rrule_str = rrule_str if rrule_str is not None else existing_chore["rrule"]
        new_start_date_str = start_date_str if start_date_str is not None else existing_chore["start_date"].isoformat()
        try:
            # Ensure the start date is timezone-aware to prevent errors.
            start_date = parse(new_start_date_str)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=datetime.timezone.utc)
            
            rule = rrulestr(new_rrule_str, dtstart=start_date)

            # Recalculate the next due date based on the new schedule.
            yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
            next_due_date = rule.after(yesterday)

            if next_due_date is None:
                raise ValueError("Could not determine next due date for the given rule.")

            # Add the updated schedule fields to the update document.
            update_doc["rrule"] = new_rrule_str
            update_doc["start_date"] = start_date
            update_doc["next_due_date"] = next_due_date
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid rrule or start_date: {e}",
            )

    # If no fields were provided to update, there's nothing to do.
    if not update_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )

    # Perform the update operation in the database.
    result = await recurring_chores_coll.update_one(
        {"_id": recurring_chore_obj_id},
        {"$set": update_doc},
    )

    if result.modified_count == 1:
        return {"message": "Recurring chore updated successfully."}
    else:
        # This could happen if the update resulted in no actual changes to the document.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update recurring chore.",
        )

@router.delete("/recurring-chores/{recurring_chore_id}")
async def delete_recurring_chore(recurring_chore_id: str, current_user: Annotated[User, Depends(get_current_user)]):
    """
    Deletes a specific recurring chore schedule.

    When a recurring chore schedule is deleted, it's important to also delete all the
    individual, non-completed chores that were generated from it to avoid clutter.

    Parameters:
    - `recurring_chore_id`: The ID of the recurring chore schedule to delete.
    - `current_user`: The authenticated user.

    Returns:
    - A dictionary containing a success message.

    Raises:
    - `HTTPException(403, ...)`: If the user is not in a group.
    - `HTTPException(404, ...)`: If the recurring chore is not found.
    - `HTTPException(500, ...)`: If the database deletion fails.
    """
    if not current_user.group_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be in a group to delete a recurring chore.",
        )

    group_id = ObjectId(current_user.group_ids[0])
    recurring_chore_obj_id = ObjectId(recurring_chore_id)

    # Verify ownership before deleting.
    recurring_chore = await recurring_chores_coll.find_one({"_id": recurring_chore_obj_id, "group_id": group_id})
    if not recurring_chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring chore not found in your group.",
        )

    # Important: Clean up chores that were generated by this recurring schedule.
    # We use `delete_many` to remove all documents matching the filter.
    # Note: This will also delete *completed* chores. Depending on the desired behavior,
    # you might want to only delete non-completed chores, e.g., by adding `"is_completed": False`
    # to the filter. For now, we delete all of them for simplicity.
    await chores_coll.delete_many({"recurring_chore_id": recurring_chore_obj_id})

    # Delete the recurring chore schedule itself.
    result = await recurring_chores_coll.delete_one({"_id": recurring_chore_obj_id})

    if result.deleted_count == 1:
        return {"message": "Recurring chore deleted successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recurring chore.",
        )