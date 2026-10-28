from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.portal_client import PortalClient
from app.routers.meters import router as meters_router
from app.routers.transformers import router as transformers_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    portal = PortalClient()

    try:
        portal.login()
        app.state.portal = portal
        yield
    finally:
        portal.close()


app = FastAPI(
    title="Urja Meter API",
    description="A documented API service over the Urja Meter Ops portal.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(meters_router)
app.include_router(transformers_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}