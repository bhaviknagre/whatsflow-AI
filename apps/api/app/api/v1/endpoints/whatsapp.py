from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
)
from app.db.session import get_db
from app.schemas.whatsapp import (
    MetaConnectResponse,
    MetaSignupRequest,
    MetaSignupResponse,
    WhatsAppConnectionResponse,
)
from app.services.meta_connection import (
    MetaConnectionService,
)
from app.services.meta_oauth import (
    consume_oauth_state,
    create_oauth_state,
)
from app.services.whatsapp import (
    get_connections,
)
from app.services.whatsapp_connection import (
    save_connection,
)

router = APIRouter(
    prefix="/whatsapp",
    tags=["WhatsApp"],
)


@router.get(
    "/connections",
    response_model=list[
        WhatsAppConnectionResponse
    ],
)
def list_connections(
    current_user: CurrentUser = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    return get_connections(
        db,
        current_user.organization_id,
    )


@router.post(
    "/signup",
    response_model=MetaSignupResponse,
)
async def complete_signup(
    payload: MetaSignupRequest,
    current_user: CurrentUser = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    try:
        organization_id = consume_oauth_state(
            db,
            payload.state,
        )

        if (
            organization_id
            != current_user.organization_id
        ):
            raise ValueError(
                "OAuth state belongs to another organization"
            )

        service = MetaConnectionService()

        connection = (
            await service.exchange_and_validate(
                code=payload.code,
                waba_id=payload.waba_id,
                phone_number_id=(
                    payload.phone_number_id
                ),
            )
        )

        saved = save_connection(
            db,
            organization_id=(
                current_user.organization_id
            ),
            waba_id=connection.waba_id,
            phone_number_id=(
                connection.phone_number_id
            ),
            display_phone_number=(
                connection.display_phone_number
            ),
            verified_name=(
                connection.verified_name
            ),
            access_token=(
                connection.access_token
            ),
            expires_at=connection.expires_at,
        )

        db.commit()

        return MetaSignupResponse(
            status="connected",
            connection_id=saved.id,
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to complete Meta WhatsApp signup",
        ) from exc

@router.get(
    "/connect",
    response_model=MetaConnectResponse,
)
def connect_whatsapp(
    current_user: CurrentUser = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    state = create_oauth_state(
        db,
        current_user.organization_id,
    )

    return MetaConnectResponse(
        state=state,
    )