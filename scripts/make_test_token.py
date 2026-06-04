"""Generuje testowy JWT do klikania działających endpointów w Swaggerze (/docs).

Bez frontendu i logowania nie da się zdobyć tokenu Supabase Auth, a większość API
wymaga `Authorization: Bearer <JWT>`. Ten skrypt:
  1. seeduje komplet danych demo (idempotentnie) — dostaje org_id org demo;
  2. tworzy/aktualizuje wpis w public.users powiązany z tą org — KRYTYCZNE, bo
     api/deps.get_current_user po zdekodowaniu tokenu robi
     SELECT FROM users WHERE id = <sub>; bez wpisu zwróciłby 403;
  3. podpisuje JWT (HS256, aud="authenticated") tym samym sekretem, którym
     api/deps._decode_jwt go weryfikuje.

Token ważny 8h. Użycie:
  python scripts/make_test_token.py
Następnie w http://localhost:8000/docs → „Authorize" → wklej sam token.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jose import jwt

from api.config import get_settings
from db.supabase_client import service_client
from scripts.seed_demo_data import seed

DEMO_USER_EMAIL = "demo-admin@meterbill.local"
DEMO_USER_PASSWORD = "demo-meterbill-2026"  # tylko dla usera demo w środowisku dev
TOKEN_TTL_HOURS = 8


def _find_auth_user_id(client, email: str) -> str | None:
    """Szuka usera w Supabase Auth po emailu (idempotencja). Zwraca id albo None."""
    # list_users stronicuje; user demo zwykle jest na pierwszej stronie.
    users = client.auth.admin.list_users()
    for u in users:
        if getattr(u, "email", None) == email:
            return u.id
    return None


def ensure_demo_user(client, org_id: str) -> str:
    """Zapewnia usera demo w Auth + profil w public.users. Zwraca user_id.

    public.users.id ma FK do auth.users(id), więc najpierw musi istnieć user w
    Supabase Auth. Tworzymy go przez Admin API (idempotentnie po emailu), a jego
    realne id wpisujemy do public.users i używamy jako `sub` w JWT.
    """
    user_id = _find_auth_user_id(client, DEMO_USER_EMAIL)
    if user_id is None:
        created = client.auth.admin.create_user(
            {
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD,
                "email_confirm": True,
            }
        )
        user_id = created.user.id

    # Profil w public.users (org_id, role). Idempotentnie po id.
    existing = (
        client.table("users").select("id").eq("id", user_id).limit(1).execute()
    ).data or []
    if existing:
        client.table("users").update({"org_id": org_id, "active": True}).eq(
            "id", user_id
        ).execute()
    else:
        client.table("users").insert(
            {
                "id": user_id,
                "org_id": org_id,
                "email": DEMO_USER_EMAIL,
                "role": "admin",
                "active": True,
            }
        ).execute()
    return user_id


def make_token(user_id: str) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": DEMO_USER_EMAIL,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=TOKEN_TTL_HOURS)).timestamp()),
        "iss": s.supabase_url,
    }
    return jwt.encode(payload, s.supabase_jwt_secret, algorithm="HS256")


def main() -> int:
    client = service_client()
    org_id, _building_id = seed(client)
    user_id = ensure_demo_user(client, org_id)
    token = make_token(user_id)

    print()
    print(f"Token JWT (ważny {TOKEN_TTL_HOURS}h, org_id={org_id}):")
    print()
    print(token)
    print()
    print("Jak uzyc:")
    print("  1. uvicorn api.main:app --reload")
    print('  2. http://localhost:8000/docs -> przycisk "Authorize" -> wklej powyzszy token')
    print("  3. Klikaj endpointy - np. GET /api/v1/buildings zwroci budynek demo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
