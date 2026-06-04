"""Schematy najemców (lokatorów rozliczanych za energię)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TenantCreate(BaseModel):
    building_id: UUID
    name: str
    email: str  # bez EmailStr — nie wciągamy email-validator (zgodnie z konwencją zależności)
    unit_no: str  # nr lokalu, np. "U1", "M3"
    nip: str | None = None  # jeśli firma
    active: bool = True


class TenantUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    unit_no: str | None = None
    nip: str | None = None
    active: bool | None = None


class TenantOut(BaseModel):
    id: UUID
    building_id: UUID
    name: str
    email: str
    unit_no: str
    nip: str | None = None
    active: bool = True
    created_at: datetime | None = None
