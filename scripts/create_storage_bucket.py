"""Tworzy prywatny bucket Storage `invoices` w projekcie Supabase.

Bez tego bucketa `core/invoice_delivery.get_or_build_pdf` wywala się przy uploadzie PDF.
Skrypt jest idempotentny — ponowne uruchomienie nie nadpisuje istniejącego bucketa,
tylko raportuje, że już jest. Działa na SERVICE_KEY (uprawnienia do zarządzania Storage).

Parametry bucketa (zgodne z core/invoice_delivery.py):
  - nazwa:   invoices
  - public:  OFF (prywatny; portal najemcy dostanie podpisane URL-e w fazie 4)
  - MIME:    tylko application/pdf (jedyne, co tam trafia)

Użycie:
  .venv/Scripts/python.exe scripts/create_storage_bucket.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Pozwól uruchamiać skrypt z dowolnego katalogu (import api/core/db z roota repo).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.invoice_delivery import STORAGE_BUCKET
from db.supabase_client import service_client


def main() -> int:
    client = service_client()
    storage = client.storage

    existing = {b.name for b in storage.list_buckets()}
    if STORAGE_BUCKET in existing:
        print(f"Bucket '{STORAGE_BUCKET}' już istnieje — nic nie robię.")
        return 0

    storage.create_bucket(
        STORAGE_BUCKET,
        options={
            "public": False,
            "allowed_mime_types": ["application/pdf"],
        },
    )
    print(f"Utworzono prywatny bucket '{STORAGE_BUCKET}' (public=OFF, MIME=application/pdf).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
