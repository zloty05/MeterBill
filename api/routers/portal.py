"""Portal najemcy — publiczny, autoryzacja przez portal_token w URL (bez JWT).

Cały kontekst (najemca, budynek, org) wyprowadzamy z tokenu przez
core.portal_auth.resolve_tenant_by_token. Każdy endpoint widzi WYŁĄCZNIE dane
tego jednego najemcy — to granica izolacji portalu. Nieważny/wygasły token → 404.

Najemca NIE widzi faktur roboczych (status 'draft') — tylko wystawione.
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi import status as http_status

from api.schemas.portal import (
    PortalInvoiceOut,
    PortalOverviewOut,
    PortalTenantOut,
)
from api.schemas.readings import ReadingOut
from core.invoice_delivery import InvoiceNotFound, get_or_build_pdf
from core.portal_auth import PortalTokenInvalid, resolve_tenant_by_token
from db.supabase_client import service_client

router = APIRouter(prefix="/portal", tags=["portal"])

# Statusy faktur widoczne dla najemcy (bez 'draft' — to robocza wersja zarządcy).
_VISIBLE_STATUSES = ("ready", "sent", "paid", "overdue")


def _tenant_or_404(client, token: str) -> dict:
    """Waliduje token i zwraca najemcę; mapuje PortalTokenInvalid na 404."""
    try:
        return resolve_tenant_by_token(client, token)
    except PortalTokenInvalid as exc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


def _tenant_invoices(client, tenant_id: str) -> list[dict]:
    """Faktury najemcy widoczne w portalu (bez draft), najnowsze pierwsze."""
    rows = (
        client.table("invoices")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    ).data or []
    return [r for r in rows if r.get("status") in _VISIBLE_STATUSES]


@router.get("/{token}/overview", response_model=PortalOverviewOut)
def portal_overview(token: str):
    """Przegląd: dane najemcy + ostatnia wystawiona faktura."""
    client = service_client()
    tenant = _tenant_or_404(client, token)
    building = tenant.get("building") or {}

    invoices = _tenant_invoices(client, tenant["id"])
    latest = PortalInvoiceOut(**invoices[0]) if invoices else None

    return PortalOverviewOut(
        tenant=PortalTenantOut(
            name=tenant["name"],
            unit_no=tenant["unit_no"],
            building_name=building.get("name"),
            building_address=building.get("address"),
        ),
        latest_invoice=latest,
    )


@router.get("/{token}/readings", response_model=list[ReadingOut])
def portal_readings(token: str):
    """Historia odczytów liczników przypisanych do najemcy, najnowsze pierwsze."""
    client = service_client()
    tenant = _tenant_or_404(client, token)

    assignments = (
        client.table("meter_assignments")
        .select("meter_id")
        .eq("tenant_id", tenant["id"])
        .execute()
    ).data or []
    meter_ids = [a["meter_id"] for a in assignments]
    if not meter_ids:
        return []

    res = (
        client.table("readings")
        .select("*")
        .in_("meter_id", meter_ids)
        .order("read_at", desc=True)
        .execute()
    )
    return [ReadingOut(**row) for row in (res.data or [])]


@router.get("/{token}/invoices", response_model=list[PortalInvoiceOut])
def portal_invoices(token: str):
    """Lista faktur najemcy (bez szkiców)."""
    client = service_client()
    tenant = _tenant_or_404(client, token)
    return [PortalInvoiceOut(**row) for row in _tenant_invoices(client, tenant["id"])]


@router.get("/{token}/invoices/{invoice_id}/pdf")
def portal_invoice_pdf(token: str, invoice_id: str):
    """PDF faktury — tylko jeśli należy do tego najemcy i nie jest szkicem."""
    client = service_client()
    tenant = _tenant_or_404(client, token)

    rows = (
        client.table("invoices")
        .select("tenant_id, status")
        .eq("id", invoice_id)
        .limit(1)
        .execute()
    ).data or []
    if (
        not rows
        or str(rows[0]["tenant_id"]) != str(tenant["id"])
        or rows[0].get("status") not in _VISIBLE_STATUSES
    ):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Nie znaleziono faktury"
        )

    try:
        pdf_bytes, pdf_path = get_or_build_pdf(client, tenant["org_id"], invoice_id)
    except InvoiceNotFound as exc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    filename = pdf_path.rsplit("/", 1)[-1]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
