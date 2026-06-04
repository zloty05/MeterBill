"""Generuje klucz API gateway (X-API-Key) dla organizacji.

Gateway (PLC) autoryzuje się przez nagłówek `X-API-Key`. W bazie przechowujemy
tylko sha256 klucza (kolumna api_keys.key_hash) — plaintext widzisz TYLKO raz,
przy generowaniu. Skopiuj go do konfiguracji sterownika; nie da się go odzyskać.

Domyślnie tworzy klucz dla organizacji demo (z seed_demo_data). Inną org wskaż
przez --org-id, nazwę klucza przez --name.

Użycie:
  python scripts/make_api_key.py
  python scripts/make_api_key.py --org-id <uuid> --name "Gateway Rynek 12"

Rotacja: uruchom ponownie, by wygenerować nowy klucz; stary dezaktywuj ręcznie
(api_keys.active = false) lub usuń.
"""
from __future__ import annotations

import argparse
import hashlib
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.supabase_client import service_client
from scripts.seed_demo_data import seed

KEY_PREFIX_LEN = 8  # ile pierwszych znaków zapisać do identyfikacji w UI


def make_api_key(client, org_id: str, name: str) -> str:
    """Tworzy wpis w api_keys i zwraca plaintext klucza (tylko teraz dostępny)."""
    plaintext = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    client.table("api_keys").insert(
        {
            "org_id": org_id,
            "name": name,
            "key_hash": key_hash,
            "key_prefix": plaintext[:KEY_PREFIX_LEN],
            "active": True,
        }
    ).execute()
    return plaintext


def main() -> int:
    parser = argparse.ArgumentParser(description="Generuje klucz API gateway (X-API-Key).")
    parser.add_argument("--org-id", help="UUID organizacji (domyślnie: org demo z seed).")
    parser.add_argument("--name", default="Gateway", help='Nazwa klucza, np. "Gateway Rynek 12".')
    args = parser.parse_args()

    client = service_client()
    org_id = args.org_id
    if org_id is None:
        org_id, _building_id = seed(client)

    plaintext = make_api_key(client, org_id, args.name)

    print()
    print(f"Klucz API utworzony (org_id={org_id}, nazwa={args.name!r}).")
    print("UWAGA: plaintext widoczny TYLKO teraz — w bazie jest tylko hash.")
    print()
    print(plaintext)
    print()
    print("Jak użyć:")
    print("  Nagłówek HTTP gateway:  X-API-Key: <powyższy klucz>")
    print("  Cel:                    POST /api/v1/readings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
