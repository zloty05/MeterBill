"""Faktury: generowanie (silnik taryfowy), lista, szczegóły, wysyłka, status."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import status as http_status

from api.config import get_settings
from api.deps import get_current_org
from api.schemas.invoices import (
    GenerateInvoicesRequest,
    GenerateInvoicesResponse,
    InvoiceLineOut,
    InvoiceOut,
    SendInvoiceResponse,
    SkippedTenant,
    UpdateStatusRequest,
)
from core.invoice_delivery import (
    InvoiceNotFound,
    ResendNotConfigured,
    get_or_build_pdf,
    send_invoice_email,
)
from core.invoice_service import generate_invoices_for_building
from db.supabase_client import service_client

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/generate", response_model=GenerateInvoicesResponse)
def generate_invoices(
    body: GenerateInvoicesRequest,
    org_id: str = Depends(get_current_org),
):
    """Uruchamia silnik taryfowy dla budynku w zadanym okresie.

    Generuje faktury (status 'draft') dla aktywnych najemców. Najemcy bez
    kompletu danych (odczyt/przypisanie/taryfa) lub z istniejącą fakturą na ten
    okres trafiają do listy `skipped` — nie blokują pozostałych.
    """
    settings = get_settings()
    try:
        result = generate_invoices_for_building(
            service_client(),
            org_id=org_id,
            building_id=str(body.building_id),
            period_from=body.period_from,
            period_to=body.period_to,
            due_days=settings.invoice_due_days,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return GenerateInvoicesResponse(
        generated=[
            InvoiceOut(**g.invoice, lines=[InvoiceLineOut(**l) for l in g.lines])
            for g in result.generated
        ],
        skipped=[
            SkippedTenant(
                tenant_id=s.tenant_id, tenant_name=s.tenant_name, reason=s.reason
            )
            for s in result.skipped
        ],
    )


@router.post("/run-scheduler", status_code=http_status.HTTP_202_ACCEPTED)
def run_scheduler(_org_id: str = Depends(get_current_org)):
    """Ręcznie wyzwala task schedulera (to samo co Celery Beat robi cyklicznie).

    Wrzuca zadanie do kolejki Celery i zwraca jego id — wykonanie idzie tym
    samym torem co harmonogram (poprzedni miesiąc, wszystkie budynki/org, draft).
    Do testów i awaryjnego dogenerowania. Operacja administracyjna (generuje dla
    wszystkich org); docelowo ograniczyć do roli admin.
    """
    # Import lokalny — moduł Celery ciągnie broker/Redis, którego API nie potrzebuje.
    from tasks.celery_tasks import generate_all_invoices

    task = generate_all_invoices.delay()
    return {"task_id": task.id, "status": "queued"}


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    tenant_id: str | None = None,
    status: str | None = None,
    org_id: str = Depends(get_current_org),
):
    """Lista faktur organizacji z opcjonalnym filtrem po najemcy i statusie."""
    query = service_client().table("invoices").select("*").eq("org_id", org_id)
    if tenant_id:
        query = query.eq("tenant_id", tenant_id)
    if status:
        query = query.eq("status", status)
    res = query.order("created_at", desc=True).execute()
    return [InvoiceOut(**row) for row in (res.data or [])]


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, org_id: str = Depends(get_current_org)):
    """Szczegóły faktury wraz z pozycjami (invoice_lines)."""
    client = service_client()
    res = (
        client.table("invoices")
        .select("*")
        .eq("id", invoice_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Nie znaleziono faktury")

    lines_res = (
        client.table("invoice_lines")
        .select("*")
        .eq("invoice_id", invoice_id)
        .order("sort_order")
        .execute()
    )
    return InvoiceOut(
        **rows[0], lines=[InvoiceLineOut(**l) for l in (lines_res.data or [])]
    )


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: str, org_id: str = Depends(get_current_org)):
    """Renderuje (i archiwizuje w Storage) PDF faktury i zwraca go do podglądu."""
    try:
        pdf_bytes, pdf_path = get_or_build_pdf(service_client(), org_id, invoice_id)
    except InvoiceNotFound as exc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    filename = pdf_path.rsplit("/", 1)[-1]  # np. FV-001-04-2026.pdf
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/{invoice_id}/send", response_model=SendInvoiceResponse)
def send_invoice(invoice_id: str, org_id: str = Depends(get_current_org)):
    """Wysyła email z PDF (Resend) i oznacza fakturę jako 'sent'."""
    try:
        result = send_invoice_email(
            service_client(), org_id, invoice_id, get_settings()
        )
    except ResendNotConfigured as exc:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except InvoiceNotFound as exc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return SendInvoiceResponse(**result)


@router.patch("/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    body: UpdateStatusRequest,
    invoice_id: str,
    org_id: str = Depends(get_current_org),
):
    """Ręczne oznaczenie statusu/płatności (MVP — bez integracji bankowej).

    Przy przejściu na 'paid' ustawiamy paid_at; przy odznaczeniu czyścimy.
    """
    client = service_client()
    patch: dict = {"status": body.status}
    if body.status == "paid":
        patch["paid_at"] = datetime.now(timezone.utc).isoformat()
    else:
        patch["paid_at"] = None

    res = (
        client.table("invoices")
        .update(patch)
        .eq("id", invoice_id)
        .eq("org_id", org_id)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Nie znaleziono faktury"
        )

    lines_res = (
        client.table("invoice_lines")
        .select("*")
        .eq("invoice_id", invoice_id)
        .order("sort_order")
        .execute()
    )
    return InvoiceOut(
        **rows[0], lines=[InvoiceLineOut(**l) for l in (lines_res.data or [])]
    )
