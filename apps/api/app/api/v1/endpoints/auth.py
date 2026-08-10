import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth import (
    AuthenticationError,
    authenticate_user,
    create_tokens,
    register_user,
)
from app.services.sessions import get_active_session, revoke_session

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

REFRESH_COOKIE_PATH = f"{settings.API_V1_PREFIX}/auth"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    response: Response,
    data: RegisterRequest,
    db: Session = Depends(get_db),
):

    try:
        user, _organization = register_user(
            db,
            data,
        )

        tokens = create_tokens(
            db,
            user,
            user_agent=None,
            ip_address=None,
        )

        _set_refresh_cookie(response, tokens["refresh_token"])

        return {"access_token": tokens["access_token"]}

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    response: Response,
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    try:
        user = authenticate_user(
            db,
            data,
        )

        tokens = create_tokens(
            db,
            user,
            user_agent=None,
            ip_address=None,
        )

        _set_refresh_cookie(response, tokens["refresh_token"])

        return {"access_token": tokens["access_token"]}

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh session missing",
        )

    session = get_active_session(
        db,
        refresh_token,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh session",
        )

    try:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    user = db.get(User, session.user_id)

    if not user or not user.is_active:
        revoke_session(db, session)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Rotate the refresh token.
    revoke_session(db, session)

    tokens = create_tokens(db, user)

    _set_refresh_cookie(response, tokens["refresh_token"])

    return {"access_token": tokens["access_token"]}


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token:
        session = get_active_session(
            db,
            refresh_token,
        )

        if session:
            revoke_session(
                db,
                session,
            )

    response.delete_cookie(
        key="refresh_token",
        path=REFRESH_COOKIE_PATH,
    )

    return {"message": "Logged out successfully"}
