"""Portal najemcy — walidacja tokenu dostępu i rotacja.

Portal jest publiczny (bez JWT): najemca wchodzi przez link z unikalnym tokenem
(tenants.portal_token, UUID). Cały kontekst (najemca, budynek, org) wyprowadzamy
WYŁĄCZNIE z tokenu — nie z nagłówka auth. To jest granica izolacji portalu.

Token jest ważny `portal_token_ttl_days` (domyślnie 90 dni, ENERGYBILL_MVP_PROMPT
l. 429). Generowany/rotowany przy wysyłce faktury (invoice_delivery), tak by każda
wysyłka odświeżała dostęp najemcy.

I/O żyje tu (zapytania do Supabase); router tylko mapuje wyjątek na 404.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


class PortalTokenInvalid(LookupError):
    """Token nie istnieje, wygasł lub najemca jest nieaktywny.

    Jeden wyjątek na wszystkie przypadki — nie zdradzamy najemcy, który z nich
    zaszedł (router mapuje na 404).
    """


def resolve_tenant_by_token(client, token: str) -> dict:
    """Zwraca najemcę dla ważnego tokenu wraz z org_id (przez building → org).

    Waliduje: token istnieje, najemca aktywny, token_expires_at w przyszłości
    (lub pusty — traktowany jako bezterminowy fallback nie jest dozwolony: brak
    daty = nieważny, bo token bez daty nigdy nie został poprawnie wydany).
    Rzuca PortalTokenInvalid w każdym innym wypadku. Dorzuca klucz "org_id".
    """
    if not token:
        raise PortalTokenInvalid("Brak tokenu")

    rows = (
        client.table("tenants")
        .select("id, building_id, name, email, unit_no, active, token_expires_at")
        .eq("portal_token", token)
        .limit(1)
        .execute()
    ).data or []
    if not rows:
        raise PortalTokenInvalid("Nieprawidłowy token portalu")

    tenant = rows[0]
    if not tenant.get("active"):
        raise PortalTokenInvalid("Dostęp nieaktywny")

    expires = tenant.get("token_expires_at")
    if not expires or _parse_dt(expires) < datetime.now(timezone.utc):
        raise PortalTokenInvalid("Token wygasł")

    building = (
        client.table("buildings")
        .select("id, org_id, name, address")
        .eq("id", tenant["building_id"])
        .limit(1)
        .execute()
    ).data or []
    if not building:
        raise PortalTokenInvalid("Nieprawidłowy token portalu")

    tenant["org_id"] = building[0]["org_id"]
    tenant["building"] = building[0]
    return tenant


def ensure_portal_token(client, tenant_id: str, ttl_days: int = 90) -> str:
    """Zapewnia ważny portal_token najemcy; rotuje gdy brak lub wygasł. Zwraca token.

    Wołane przy wysyłce faktury — „regenerowany przy wysyłce kolejnej faktury"
    (ENERGYBILL_MVP_PROMPT l. 429). Idempotentne: ważny token zostaje (przedłużamy
    tylko jego ważność? Nie — zachowujemy istniejący token i jego datę, by link w
    już wysłanych mailach nie przestał działać przed czasem). Generuje nowy tylko
    gdy token nie istnieje lub minęła data ważności.
    """
    rows = (
        client.table("tenants")
        .select("portal_token, token_expires_at")
        .eq("id", tenant_id)
        .limit(1)
        .execute()
    ).data or []
    if not rows:
        return ""  # brak najemcy — nic nie robimy (wysyłka i tak by padła wcześniej)

    current = rows[0]
    token = current.get("portal_token")
    expires = current.get("token_expires_at")
    valid = bool(token) and bool(expires) and _parse_dt(expires) >= datetime.now(
        timezone.utc
    )
    if valid:
        return token

    new_token = str(uuid.uuid4())
    new_expires = (datetime.now(timezone.utc) + timedelta(days=ttl_days)).isoformat()
    client.table("tenants").update(
        {"portal_token": new_token, "token_expires_at": new_expires}
    ).eq("id", tenant_id).execute()
    return new_token


def _parse_dt(value) -> datetime:
    """Parsuje timestamptz z bazy (string ISO) do aware datetime (UTC)."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
