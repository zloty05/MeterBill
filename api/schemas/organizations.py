"""Schematy organizacji (dane zarządcy — sprzedawcy na fakturze)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

OrgPlan = Literal["free", "pro", "enterprise"]


class OrgOut(BaseModel):
    id: UUID
    name: str
    nip: str | None = None
    address: str | None = None
    bank_account: str | None = None
    plan: OrgPlan = "free"
    created_at: datetime | None = None


class OrgUpdate(BaseModel):
    # Wszystkie pola opcjonalne — PATCH aktualizuje tylko przekazane (exclude_unset).
    name: str | None = None
    nip: str | None = None
    address: str | None = None
    bank_account: str | None = None
