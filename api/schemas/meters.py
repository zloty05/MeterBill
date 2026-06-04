"""Schematy liczników (podliczniki M-Bus) i przypisań licznik↔najemca."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

MeterProtocol = Literal["mbus", "modbus", "opcua", "manual"]


class MeterCreate(BaseModel):
    building_id: UUID
    serial_no: str
    tariff_id: UUID | None = None
    mbus_address: str | None = None  # adres M-Bus (hex, np. "05")
    protocol: MeterProtocol = "mbus"
    ppe_code: str | None = None
    tariff_group: str = "G11"
    label: str | None = None  # np. "Lokal U1 – parter"


class MeterUpdate(BaseModel):
    serial_no: str | None = None
    tariff_id: UUID | None = None
    mbus_address: str | None = None
    protocol: MeterProtocol | None = None
    ppe_code: str | None = None
    tariff_group: str | None = None
    label: str | None = None


class MeterOut(BaseModel):
    id: UUID
    building_id: UUID
    tariff_id: UUID | None = None
    serial_no: str
    mbus_address: str | None = None
    protocol: MeterProtocol = "mbus"
    ppe_code: str | None = None
    tariff_group: str = "G11"
    label: str | None = None
    created_at: datetime | None = None


# --- Przypisania licznik↔najemca (meter_assignments) ---


class AssignmentCreate(BaseModel):
    tenant_id: UUID
    valid_from: date
    valid_to: date | None = None  # None = przypisanie aktywne (otwarte)


class AssignmentOut(BaseModel):
    id: UUID
    tenant_id: UUID
    meter_id: UUID
    valid_from: date
    valid_to: date | None = None
