
from fastapi import APIRouter, HTTPException, Query, Request

from app.clients.portal_client import PortalClient, PortalClientError
from app.schemas.transformer import TransformerResponse

router = APIRouter(
    prefix="/api/v1/transformers",
    tags=["Transformers"],
)


@router.get("", response_model=TransformerResponse)
def list_transformers(
    request: Request,
    page: int = Query(default=1, ge=1),
):
    """List distribution transformers."""
    portal: PortalClient = request.app.state.portal

    try:
        return portal.list_transformers(page=page)
    except PortalClientError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve transformer data from the portal.",
        ) from exc
