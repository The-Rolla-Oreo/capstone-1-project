from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile

from backend.celery_worker import upload_pfp_task
from backend.helpers.helper_auth import get_current_user
from backend.models import User


router = APIRouter()

ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]


@router.post("/set-profile-picture")
async def set_profile_pic(
    current_user: Annotated[User, Depends(get_current_user)],
    pfp: UploadFile,
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

    pfp_data = await pfp.read()
    upload_pfp_task.delay(user_dict=current_user.model_dump(), pfp_data=pfp_data)

    return {"msg": "Profile picture upload in progress."}
