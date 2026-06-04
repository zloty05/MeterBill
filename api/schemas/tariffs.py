"""Schematy taryf (szablony) i ich składników."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ComponentType = Literal["per_kwh", "monthly_fixed", "monthly_allocated"]
AllocationMethod = Literal["proportional", "equal"]


class ComponentCreate(BaseModel):
    name: str
    component_type: ComponentType
    unit_price: Decimal
    unit: str = "zł/kWh"  # zł/kWh | zł/mc
    vat_rate: Decimal = Decimal("23")
    allocation_method: AllocationMethod = "proportional"
    sort_order: int = 0


class ComponentOut(BaseModel):
    id: UUID
    tariff_id: UUID
    name: str
    component_type: ComponentType
    unit_price: Decimal
    unit: str = "zł/kWh"
    vat_rate: Decimal = Decimal("23")
    allocation_method: AllocationMethod = "proportional"
    sort_order: int = 0


class TariffCreate(BaseModel):
    name: str
    valid_from: date
    tariff_group: str = "G11"
    margin_pct: Decimal = Decimal("0")  # marża zarządcy w %
    vat_rate: Decimal = Decimal("23")
    source_doc: str | None = None  # nr faktury źródłowej
    valid_to: date | None = None


class TariffUpdate(BaseModel):
    name: str | None = None
    tariff_group: str | None = None
    margin_pct: Decimal | None = None
    vat_rate: Decimal | None = None
    source_doc: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None


class TariffOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    tariff_group: str = "G11"
    margin_pct: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("23")
    source_doc: str | None = None
    valid_from: date
    valid_to: date | None = None
    components: list[ComponentOut] = Field(default_factory=list)
