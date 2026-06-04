"""Schematy budynków zarządcy."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BuildingCreate(BaseModel):
    name: str
    address: str
    main_meter_ppe: str | None = None  # kod PPE licznika głównego


class BuildingUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    main_meter_ppe: str | None = None


class BuildingOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    address: str
    main_meter_ppe: str | None = None
    created_at: datetime | None = None
