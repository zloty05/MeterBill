"""Portal najemcy — publiczny, autoryzacja przez portal_token (bez JWT)."""
from fastapi import APIRouter

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/{token}/overview")
def portal_overview(token: str):
    raise NotImplementedError


@router.get("/{token}/readings")
def portal_readings(token: str):
    raise NotImplementedError


@router.get("/{token}/invoices")
def portal_invoices(token: str):
    raise NotImplementedError


@router.get("/{token}/invoices/{invoice_id}/pdf")
def portal_invoice_pdf(token: str, invoice_id: str):
    raise NotImplementedError
