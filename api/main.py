"""EnergyBill API — punkt wejścia FastAPI.

Spina routery pod prefiksem /api/v1, konfiguruje CORS i healthcheck.
Auth: JWT (Supabase) dla panelu, X-API-Key dla gateway, token dla portalu.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routers import (
    buildings,
    invoices,
    meters,
    organizations,
    portal,
    readings,
    tariffs,
    tenants,
)

settings = get_settings()

app = FastAPI(
    title="EnergyBill API",
    version="0.1.0",
    description="SaaS do automatycznego rozliczania energii elektrycznej.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(organizations.router, prefix=API_PREFIX)
app.include_router(buildings.router, prefix=API_PREFIX)
app.include_router(meters.router, prefix=API_PREFIX)
app.include_router(readings.router, prefix=API_PREFIX)
app.include_router(tenants.router, prefix=API_PREFIX)
app.include_router(tariffs.router, prefix=API_PREFIX)
app.include_router(invoices.router, prefix=API_PREFIX)
app.include_router(portal.router, prefix=API_PREFIX)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "environment": settings.environment}
