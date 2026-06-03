"""Schematy Pydantic dla endpointów faktur (generowanie, lista, szczegóły)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class GenerateInvoicesRequest(BaseModel):
    """Body POST /invoices/generate."""

    building_id: UUID
    period_from: date
    period_to: date

    @model_validator(mode="after")
    def _check_period(self) -> "GenerateInvoicesRequest":
        if self.period_to < self.period_from:
            raise ValueError("period_to nie może być wcześniejsze niż period_from")
        return self


class InvoiceLineOut(BaseModel):
    """Pozycja faktury (wiersz invoice_lines)."""

    label: str
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    net_amount: Decimal | None = None
    vat_rate: Decimal | None = None
    component_id: UUID | None = None
    sort_order: int = 0


class InvoiceOut(BaseModel):
    """Faktura (wiersz invoices); lines wypełnione w widoku szczegółów."""

    id: UUID
    tenant_id: UUID
    invoice_no: str
    period_from: date
    period_to: date
    kwh_consumed: Decimal | None = None
    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    gross_amount: Decimal | None = None
    status: str
    due_date: date | None = None
    is_estimated: bool = False
    issued_date: date | None = None
    sent_at: datetime | None = None
    paid_at: datetime | None = None
    pdf_path: str | None = None
    created_at: datetime | None = None
    lines: list[InvoiceLineOut] = Field(default_factory=list)


class SkippedTenant(BaseModel):
    """Najemca pominięty przy generowaniu wraz z powodem."""

    tenant_id: UUID
    tenant_name: str
    reason: str


class GenerateInvoicesResponse(BaseModel):
    """Wynik POST /invoices/generate."""

    generated: list[InvoiceOut] = Field(default_factory=list)
    skipped: list[SkippedTenant] = Field(default_factory=list)


# Statusy zgodne z ENUM invoice_status w migracji 001.
InvoiceStatus = Literal["draft", "ready", "sent", "paid", "overdue"]


class UpdateStatusRequest(BaseModel):
    """Body PATCH /invoices/{id}/status — ręczna zmiana statusu (MVP, bez banku)."""

    status: InvoiceStatus


class SendInvoiceResponse(BaseModel):
    """Wynik POST /invoices/{id}/send."""

    status: str
    sent_at: datetime | None = None
    email_id: str | None = None
