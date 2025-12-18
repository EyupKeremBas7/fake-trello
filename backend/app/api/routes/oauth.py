"""
OAuth API Routes - Google OAuth2 authentication.
"""
import secrets
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.config import settings
from app.core.security import create_access_token
from app.models.users import User

router = APIRouter(prefix="/oauth", tags=["oauth"])

oauth = OAuth()

if settings.google_oauth_enabled:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@router.get("/google/login")
async def google_login(request: Request):
    """Redirect to Google OAuth login."""
    if not settings.google_oauth_enabled:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    
    redirect_uri = f"{settings.FRONTEND_HOST}/oauth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, session: SessionDep):
    """Handle Google OAuth callback."""
    if not settings.google_oauth_enabled:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")
    
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")
    
    user = session.exec(
        select(User).where(User.email == email, User.is_deleted == False)
    ).first()
    
    if not user:
        user = User(
            email=email,
            full_name=user_info.get("name"),
            hashed_password=secrets.token_urlsafe(32),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    return RedirectResponse(
        url=f"{settings.FRONTEND_HOST}/oauth/success?token={access_token}"
    )


@router.get("/status")
async def oauth_status():
    """Check OAuth configuration status."""
    return {
        "google_enabled": settings.google_oauth_enabled,
    }
