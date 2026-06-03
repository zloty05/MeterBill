"""Faktury: generowanie (silnik taryfowy), lista, wysyłka, status."""
from fastapi import APIRouter, Depends

from api.deps import get_current_org

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/generate")
def generate_invoices(org_id: str = Depends(get_current_org)):
    """Uruchamia silnik taryfowy. Body: {building_id, period_from, period_to}."""
    raise NotImplementedError


@router.get("")
def list_invoices(
    tenant_id: str | None = None,
    status: str | None = None,
    org_id: str = Depends(get_current_org),
):
    raise NotImplementedError


@router.get("/{invoice_id}")
def get_invoice(invoice_id: str, org_id: str = Depends(get_current_org)):
    raise NotImplementedError


@router.post("/{invoice_id}/send")
def send_invoice(invoice_id: str, org_id: str = Depends(get_current_org)):
    """Wysyła email z PDF (Resend)."""
    raise NotImplementedError


@router.patch("/{invoice_id}/status")
def update_invoice_status(invoice_id: str, org_id: str = Depends(get_current_org)):
    """Ręczne oznaczenie płatności (MVP — bez integracji bankowej)."""
    raise NotImplementedError
