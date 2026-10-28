from fastapi import APIRouter, HTTPException, Query, Request
from app.schemas.meter import (
    MeterSearchResponse,
    GeoResponse,
)
from app.schemas.energy import EnergyResponse
from app.clients.portal_client import (
    PortalClient,
    PortalClientError,
)

router = APIRouter(
    prefix="/api/v1/meters",
    tags=["Meters"],
)


@router.get("", response_model=MeterSearchResponse)
def list_meters(
    request: Request,
    q: str = Query(default="", max_length=100),
    page: int = Query(default=1, ge=1),
):
    """Search meter records from the Urja Meter Ops portal."""

    portal: PortalClient = request.app.state.portal

    try:
        return portal.search_meters(query=q, page=page)
    except PortalClientError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve meter data from the portal.",
        ) from exc
    

@router.get("/{meter_id}/geo", response_model=GeoResponse)
def get_meter_geo(meter_id: str, request: Request):
    """Get geographic coordinates for a meter."""
    portal: PortalClient = request.app.state.portal

    try:
        return portal.get_meter_geo(meter_id)
    except PortalClientError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve meter location from the portal.",
        ) from exc


@router.get("/{meter_id}/energy", response_model=EnergyResponse)
def get_meter_energy(meter_id: str, request: Request):
    """Get consumption history for a meter."""
    portal: PortalClient = request.app.state.portal

    try:
        return portal.get_meter_energy(meter_id)
    except PortalClientError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve meter energy data from the portal.",
        ) from exc
