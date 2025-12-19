from fastapi import APIRouter

from app.api.routes import (
    activity,
    boards,
    cards,
    checklists,
    comments,
    invitations,
    lists,
    login,
    notifications,
    private,
    uploads,
    users,
    utils,
    workspaces,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(boards.router)
api_router.include_router(workspaces.router)
api_router.include_router(cards.router)
api_router.include_router(lists.router)
api_router.include_router(checklists.router)
api_router.include_router(comments.router)
api_router.include_router(notifications.router)
api_router.include_router(invitations.router)
api_router.include_router(uploads.router)
api_router.include_router(activity.router)

from app.api.routes import oauth

api_router.include_router(oauth.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
