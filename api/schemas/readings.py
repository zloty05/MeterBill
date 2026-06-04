"""Schematy odczytów liczników (read-only w panelu; tworzenie idzie torem gateway)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

ReadingType = Literal["remote", "physical", "estimated"]


class ReadingOut(BaseModel):
    id: UUID
    meter_id: UUID
    read_at: datetime
    read_type: ReadingType = "remote"
    value_kwh: Decimal
    power_kw: Decimal | None = None
    is_estimated: bool = False
    source: str | None = None
    created_at: datetime | None = None
