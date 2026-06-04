"""Generuje fakturę demo end-to-end: silnik → PDF → (opcjonalnie) wysyłka e-mail.

Wymaga wcześniejszego `scripts/seed_demo_data.py`. Łączy istniejące funkcje:
  1. core.invoice_service.generate_invoices_for_building → faktura ze statusem 'draft'
  2. core.invoice_delivery.get_or_build_pdf → render PDF + upload do bucketa 'invoices';
     kopia zapisywana lokalnie do ./out do podejrzenia
  3. core.invoice_delivery.send_invoice_email (tylko z flagą --send) → Resend + status 'sent'

Render PDF (WeasyPrint) wymaga natywnych libów cairo/pango — uruchamiaj w kontenerze
(`docker compose run --rm api python scripts/generate_demo_invoice.py`). Na Windows bez GTK
krok renderu rzuci OSError.

Idempotencja: ponowne generowanie tego samego okresu trafia do `skipped` (duplikat) — skrypt
wtedy bierze istniejącą fakturę i tylko renderuje/wysyła.

Użycie:
  python scripts/generate_demo_invoice.py            # faktura + PDF
  python scripts/generate_demo_invoice.py --send     # + wysyłka maila przez Resend
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.config import get_settings
from core.invoice_delivery import get_or_build_pdf, send_invoice_email, slug
from core.invoice_service import generate_invoices_for_building
from db.supabase_client import service_client
from scripts.seed_demo_data import DEMO_ORG_NAME

OUT_DIR = Path(__file__).resolve().parent.parent / "out"

PERIOD_FROM = date(2026, 4, 1)
PERIOD_TO = date(2026, 4, 30)


def _resolve_demo_org_building(client) -> tuple[str, str]:
    """Znajduje org_id/building_id zaseedowanej organizacji demo."""
    org = (
        client.table("organizations")
        .select("id")
        .eq("name", DEMO_ORG_NAME)
        .limit(1)
        .execute()
    ).data or []
    if not org:
        raise SystemExit(
            "Brak danych demo — uruchom najpierw scripts/seed_demo_data.py"
        )
    org_id = org[0]["id"]
    bld = (
        client.table("buildings").select("id").eq("org_id", org_id).limit(1).execute()
    ).data or []
    if not bld:
        raise SystemExit("Organizacja demo bez budynku — przeseeduj dane")
    return org_id, bld[0]["id"]


def _find_invoice(client, org_id: str) -> dict:
    """Faktura demo dla okresu (po wygenerowaniu lub z poprzedniego przebiegu)."""
    rows = (
        client.table("invoices")
        .select("*")
        .eq("org_id", org_id)
        .eq("period_from", PERIOD_FROM.isoformat())
        .eq("period_to", PERIOD_TO.isoformat())
        .limit(1)
        .execute()
    ).data or []
    if not rows:
        raise SystemExit("Nie znaleziono faktury demo dla okresu — sprawdź log generowania")
    return rows[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generuj fakturę demo (PDF + opcjonalnie mail)")
    parser.add_argument("--send", action="store_true", help="wyślij fakturę mailem (Resend)")
    args = parser.parse_args()

    client = service_client()
    org_id, building_id = _resolve_demo_org_building(client)

    # 1. Generowanie (idempotentne — duplikat trafia do skipped).
    result = generate_invoices_for_building(
        client, org_id, building_id, PERIOD_FROM, PERIOD_TO
    )
    if result.generated:
        inv = result.generated[0].invoice
        print(f"Wygenerowano fakturę {inv['invoice_no']}:")
        print(f"  netto {inv['net_amount']} / VAT {inv['vat_amount']} / brutto {inv['gross_amount']} zł")
        print(f"  status={inv['status']}, due_date={inv['due_date']}, pozycji={len(result.generated[0].lines)}")
    else:
        reasons = "; ".join(f"{s.tenant_name}: {s.reason}" for s in result.skipped)
        print(f"Nic nie wygenerowano (pewnie duplikat z poprzedniego przebiegu): {reasons}")

    invoice = _find_invoice(client, org_id)
    invoice_id = invoice["id"]

    # 2. Render PDF + upload do Storage. Kopia lokalna do ./out.
    pdf_bytes, pdf_path = get_or_build_pdf(client, org_id, invoice_id)
    OUT_DIR.mkdir(exist_ok=True)
    local_pdf = OUT_DIR / f"{slug(invoice['invoice_no'])}.pdf"
    local_pdf.write_bytes(pdf_bytes)
    print(f"PDF: {len(pdf_bytes)} B, sygnatura={pdf_bytes[:4]!r}")
    print(f"  Storage: invoices/{pdf_path}")
    print(f"  Lokalnie: {local_pdf}")

    # 3. Wysyłka maila (świadomie, tylko z --send).
    if args.send:
        settings = get_settings()
        sent = send_invoice_email(client, org_id, invoice_id, settings)
        print(f"Wysłano mail: email_id={sent.get('email_id')}, status={sent['status']}, sent_at={sent['sent_at']}")
    else:
        print("(pominięto wysyłkę — uruchom z --send, by wysłać mail)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
