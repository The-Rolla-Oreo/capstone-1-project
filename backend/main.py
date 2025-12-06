from fastapi import FastAPI

from backend.routes.auth import router as auth_router
from backend.routes.profile_management import router as profile_management_router
from backend.routes.groups import router as groups_router
from backend.routes.chores import router as chores_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(profile_management_router, prefix="/profile-management")
app.include_router(groups_router, prefix="/groups")
app.include_router(chores_router, prefix="/chores")
