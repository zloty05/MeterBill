"""Schematy portalu najemcy (widok publiczny przez token, okrojony do najemcy).

Nie eksponujemy pól wewnętrznych zarządcy (org_id, pdf_path, statusy robocze).
Reużywamy ReadingOut z odczytów; faktura ma własny, węższy widok.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class PortalTenantOut(BaseModel):
    """Dane najemcy widoczne w portalu."""

    name: str
    unit_no: str
    building_name: str | None = None
    building_address: str | None = None


class PortalInvoiceOut(BaseModel):
    """Faktura w portalu — bez pól wewnętrznych (org_id, pdf_path)."""

    id: UUID
    invoice_no: str
    period_from: date
    period_to: date
    kwh_consumed: Decimal | None = None
    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    gross_amount: Decimal | None = None
    status: str
    due_date: date | None = None
    issued_date: date | None = None
    paid_at: datetime | None = None


class PortalOverviewOut(BaseModel):
    """Przegląd portalu: najemca + ostatnia faktura."""

    tenant: PortalTenantOut
    latest_invoice: PortalInvoiceOut | None = None
