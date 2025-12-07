from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.auth import router as auth_router
from backend.routes.profile_management import router as profile_management_router
from backend.routes.groups import router as groups_router
from backend.settings import get_settings

settings = get_settings()

FRONTEND_URL = settings.FRONTEND_URL

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,

    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Content-Length"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(profile_management_router, prefix="/profile-management")

app.include_router(groups_router, prefix="/groups")
