"""Dostarczanie faktur: render PDF → archiwizacja w Supabase Storage → wysyłka e-mail (Resend).

Warstwa I/O między routerem a czystym renderem (core/pdf_renderer). Analogicznie do
invoice_service: tu żyją zapytania do bazy, upload do Storage i wywołania Resend; sam
render jest czysty i testowalny osobno.

Storage: prywatny bucket `invoices` w projekcie Supabase (utwórz go skryptem
`scripts/create_storage_bucket.py` — public=OFF, MIME=application/pdf). service_role
ma do niego dostęp; portal najemcy (faza 4) dostanie podpisane URL-e. Ścieżka pliku:
  {org_id}/{rok}/{invoice_no_slug}.pdf

Izolacja multi-tenant: każde zapytanie filtruje po org_id (backend działa na
SERVICE_KEY i omija RLS — patrz CLAUDE.md).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from core.pdf_renderer import InvoicePdfData, render_invoice_pdf, totals
from core.readings import latest_reading_at_or_before, parse_date

STORAGE_BUCKET = "invoices"


class InvoiceNotFound(LookupError):
    """Faktura nie istnieje lub nie należy do organizacji."""


class ResendNotConfigured(RuntimeError):
    """Brak konfiguracji Resend (RESEND_API_KEY / FROM_EMAIL)."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(invoice_no: str) -> str:
    """Numer faktury → bezpieczna nazwa pliku (FV/001/04/2026 → FV-001-04-2026)."""
    return invoice_no.replace("/", "-").replace("\\", "-").replace(" ", "_")


def _load_invoice_context(client, org_id: str, invoice_id: str) -> InvoicePdfData:
    """Zbiera komplet danych potrzebnych do PDF (faktura, pozycje, sprzedawca,
    nabywca, odczyty graniczne). Filtruje po org_id. Rzuca InvoiceNotFound."""
    inv_res = (
        client.table("invoices")
        .select("*")
        .eq("id", invoice_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    inv_rows = inv_res.data or []
    if not inv_rows:
        raise InvoiceNotFound("Faktura nie istnieje lub nie należy do organizacji")
    invoice = inv_rows[0]

    lines = (
        client.table("invoice_lines")
        .select("*")
        .eq("invoice_id", invoice_id)
        .order("sort_order")
        .execute()
    ).data or []

    org = (
        client.table("organizations")
        .select("name, nip, address, bank_account")
        .eq("id", org_id)
        .limit(1)
        .execute()
    ).data or [{}]

    tenant = (
        client.table("tenants")
        .select("name, email, nip, unit_no, building_id")
        .eq("id", invoice["tenant_id"])
        .limit(1)
        .execute()
    ).data or [{}]

    # Odczyty graniczne i licznik — przez aktywne przypisanie najemcy w okresie.
    reading_start, reading_end, meter = _load_meter_readings(
        client, invoice["tenant_id"], invoice
    )

    return InvoicePdfData(
        invoice=invoice,
        lines=lines,
        organization=org[0],
        tenant=tenant[0],
        reading_start=reading_start,
        reading_end=reading_end,
        meter=meter,
    )


def _load_meter_readings(client, tenant_id: str, invoice: dict):
    """Odczyt początkowy/końcowy i licznik dla okresu faktury. Best-effort —
    brak danych nie blokuje renderu (PDF pokaże 0/—)."""
    period_from = parse_date(invoice["period_from"])
    period_to = parse_date(invoice["period_to"])

    asg = (
        client.table("meter_assignments")
        .select("meter_id, valid_from, valid_to")
        .eq("tenant_id", tenant_id)
        .lte("valid_from", period_to.isoformat())
        .execute()
    ).data or []

    meter_id = None
    for a in asg:
        valid_to = a.get("valid_to")
        if valid_to is None or parse_date(valid_to) >= period_from:
            meter_id = a["meter_id"]
            break
    if meter_id is None:
        return None, None, None

    meter_rows = (
        client.table("meters")
        .select("id, serial_no, label")
        .eq("id", meter_id)
        .limit(1)
        .execute()
    ).data or []
    meter = meter_rows[0] if meter_rows else None

    reading_start = latest_reading_at_or_before(client, meter_id, period_from)
    reading_end = latest_reading_at_or_before(client, meter_id, period_to)
    return reading_start, reading_end, meter


def get_or_build_pdf(client, org_id: str, invoice_id: str) -> tuple[bytes, str]:
    """Renderuje PDF faktury, archiwizuje w Storage i zwraca (bajty, pdf_path).

    issued_date ustawiana na dziś, jeśli pusta (data wystawienia = pierwsze wydanie PDF).
    pdf_path zapisywany na fakturze (idempotentnie — upsert pliku w Storage).
    """
    data = _load_invoice_context(client, org_id, invoice_id)
    invoice = data.invoice

    # Data wystawienia — przy pierwszym renderze.
    if not invoice.get("issued_date"):
        today = date.today().isoformat()
        client.table("invoices").update({"issued_date": today}).eq(
            "id", invoice_id
        ).eq("org_id", org_id).execute()
        invoice["issued_date"] = today

    pdf_bytes = render_invoice_pdf(data)

    year = parse_date(invoice["period_from"]).year
    pdf_path = f"{org_id}/{year}/{slug(invoice['invoice_no'])}.pdf"

    # Upload (upsert, by ponowne wydanie nadpisało plik).
    storage = client.storage.from_(STORAGE_BUCKET)
    storage.upload(
        path=pdf_path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )

    if invoice.get("pdf_path") != pdf_path:
        client.table("invoices").update({"pdf_path": pdf_path}).eq(
            "id", invoice_id
        ).eq("org_id", org_id).execute()
        invoice["pdf_path"] = pdf_path

    return pdf_bytes, pdf_path


def send_invoice_email(client, org_id: str, invoice_id: str, settings) -> dict:
    """Wysyła fakturę e-mailem (PDF w załączniku) przez Resend i oznacza 'sent'.

    `settings` — obiekt z polami resend_api_key, from_email (api.config.Settings).
    Rzuca ResendNotConfigured gdy brak klucza/nadawcy, InvoiceNotFound gdy brak faktury.
    """
    if not settings.resend_api_key or not settings.from_email:
        raise ResendNotConfigured(
            "Brak konfiguracji Resend (RESEND_API_KEY / FROM_EMAIL)"
        )

    pdf_bytes, _ = get_or_build_pdf(client, org_id, invoice_id)
    data = _load_invoice_context(client, org_id, invoice_id)
    invoice = data.invoice
    tenant = data.tenant
    org = data.organization

    to_email = tenant.get("email")
    if not to_email:
        raise InvoiceNotFound("Najemca nie ma adresu e-mail")

    sums = totals(data.lines)
    subject = f"Faktura {invoice['invoice_no']} – {org.get('name', '')}".strip()
    html_body = _email_body(invoice, tenant, org, sums)

    import resend  # import leniwy (ciągnie httpx)

    resend.api_key = settings.resend_api_key
    params: resend.Emails.SendParams = {
        "from": settings.from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "attachments": [
            {
                "filename": f"{slug(invoice['invoice_no'])}.pdf",
                "content": list(pdf_bytes),
                "content_type": "application/pdf",
            }
        ],
    }
    sent = resend.Emails.send(params)
    email_id = sent.get("id") if isinstance(sent, dict) else getattr(sent, "id", None)

    sent_at = _now_iso()
    client.table("invoices").update(
        {"status": "sent", "sent_at": sent_at}
    ).eq("id", invoice_id).eq("org_id", org_id).execute()

    # Portal najemcy: zapewnij ważny token przy wysyłce (rotacja gdy brak/wygasł).
    # Best-effort — nie blokuje potwierdzenia wysyłki, jeśli się nie powiedzie.
    from core.portal_auth import ensure_portal_token

    ttl = getattr(settings, "portal_token_ttl_days", 90)
    ensure_portal_token(client, invoice["tenant_id"], ttl_days=ttl)

    return {"status": "sent", "sent_at": sent_at, "email_id": email_id}


def _money_pl(value) -> str:
    from core.pdf_renderer import format_money
    return format_money(value)


def _email_body(invoice: dict, tenant: dict, org: dict, sums: dict) -> str:
    """Treść maila z blokiem płatności (ENERGYBILL_MVP_PROMPT.md l. 631–637)."""
    gross = _money_pl(sums["gross_amount"])
    due = str(invoice.get("due_date") or "")[:10]
    bank = org.get("bank_account") or "—"
    title = f"{invoice['invoice_no']} – {tenant.get('name', '')}"
    return f"""\
<p>Dzień dobry,</p>
<p>w załączniku przesyłamy fakturę <strong>{invoice['invoice_no']}</strong>
za zużycie energii elektrycznej.</p>
<table style="border-collapse:collapse;margin:16px 0;">
  <tr><td style="padding:2px 16px 2px 0;color:#5a6b5a;">Tytuł przelewu</td><td><strong>{title}</strong></td></tr>
  <tr><td style="padding:2px 16px 2px 0;color:#5a6b5a;">Nr konta</td><td>{bank}</td></tr>
  <tr><td style="padding:2px 16px 2px 0;color:#5a6b5a;">Kwota</td><td><strong>{gross} zł</strong></td></tr>
  <tr><td style="padding:2px 16px 2px 0;color:#5a6b5a;">Termin</td><td>{due}</td></tr>
</table>
<p style="color:#8a9a8a;font-size:12px;">Wiadomość wygenerowana automatycznie przez EnergyBill.</p>
"""
