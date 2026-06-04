"""Schematy odczytów liczników (read-only w panelu; tworzenie idzie torem gateway)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

ReadingType = Literal["remote", "physical", "estimated"]


class ReadingCreate(BaseModel):
    """Odczyt przyjmowany przez gateway (PLC) na POST /readings.

    `read_at` jest opcjonalny — gdy gateway go nie poda, czas nadaje serwer
    (now UTC). Sterownik nie musi mieć zsynchronizowanego zegara.
    `meter_id` jest walidowany pod kątem przynależności do organizacji w routerze.
    """

    meter_id: UUID
    value_kwh: Decimal
    power_kw: Decimal | None = None
    read_type: ReadingType = "remote"
    is_estimated: bool = False
    source: str | None = None
    read_at: datetime | None = None

    @field_validator("value_kwh")
    @classmethod
    def _value_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("value_kwh nie może być ujemne")
        return v


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
