"""Zależności FastAPI: autoryzacja i kontekst organizacji.

Dwa tory autoryzacji:
  1. Zarządca (panel/portal API) → JWT z Supabase Auth (Bearer).
     get_current_user() weryfikuje token, get_current_org() zwraca org_id.
  2. Gateway agent (POST /readings) → X-API-Key.
     get_api_key_org() weryfikuje hash klucza i zwraca org_id.

Hybryda RLS + app-layer: nawet gdy backend działa na SERVICE_KEY (bypass RLS),
wszystkie zapytania filtrujemy po org_id zwróconym przez te zależności.
"""
import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from api.config import get_settings
from db.supabase_client import service_client

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: str          # auth.users.id
    email: str | None
    org_id: str
    role: str


# Cache JWKS (asymetryczne klucze publiczne Supabase) — pobierane raz, odświeżane
# co _JWKS_TTL. Supabase od trybu "JWT signing keys" podpisuje tokeny ES256 i
# wystawia klucz publiczny pod /auth/v1/.well-known/jwks.json.
_JWKS_TTL = 600  # sekundy
_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0.0


def _fetch_jwks(force: bool = False) -> dict:
    """Pobiera (i cache'uje) JWKS Supabase. httpx korzysta z obejścia SSL
    skonfigurowanego globalnie w db.supabase_client (MITM/Norton)."""
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if not force and _jwks_cache is not None and (now - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks_cache
    s = get_settings()
    url = f"{s.supabase_url}/auth/v1/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    _jwks_cache = resp.json()
    _jwks_fetched_at = now
    return _jwks_cache


def _jwk_for_kid(kid: str, allow_refetch: bool = True) -> dict | None:
    """Zwraca klucz JWK o danym kid; gdy brak, jednorazowo odświeża JWKS
    (rotacja kluczy po stronie Supabase)."""
    jwks = _fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    if allow_refetch:
        jwks = _fetch_jwks(force=True)
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
    return None


def _decode_jwt(token: str) -> dict:
    s = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token (nagłówek)",
        ) from exc

    alg = header.get("alg", "")
    try:
        if alg.startswith("HS"):
            # Stary tryb / token z make_test_token.py — sekret symetryczny.
            return jwt.decode(
                token,
                s.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )

        # Tryb asymetryczny (ES256/RS256) — klucz publiczny z JWKS po kid.
        kid = header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token bez identyfikatora klucza (kid)",
            )
        jwk = _jwk_for_kid(kid)
        if jwk is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nieznany klucz podpisujący token",
            )
        return jwt.decode(
            token,
            jwk,
            algorithms=[alg],
            audience="authenticated",
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy lub wygasły token",
        ) from exc


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """Weryfikuje JWT i ładuje profil usera (z org_id) z public.users."""
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Brak tokenu autoryzacji",
        )

    payload = _decode_jwt(creds.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token bez identyfikatora użytkownika",
        )

    # Profil (org_id, role) z public.users
    res = (
        service_client()
        .table("users")
        .select("id, email, org_id, role, active")
        .eq("id", user_id)
        .single()
        .execute()
    )
    profile = res.data
    if not profile or not profile.get("active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Użytkownik nieaktywny lub bez profilu",
        )

    return CurrentUser(
        id=profile["id"],
        email=profile.get("email"),
        org_id=profile["org_id"],
        role=profile.get("role", "viewer"),
    )


def get_current_org(user: CurrentUser = Depends(get_current_user)) -> str:
    """Skrót: zwraca org_id zalogowanego usera."""
    return user.org_id


def get_api_key_org(x_api_key: str | None = Header(default=None)) -> str:
    """Autoryzacja gateway agenta przez X-API-Key. Zwraca org_id."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Brak nagłówka X-API-Key",
        )

    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    res = (
        service_client()
        .table("api_keys")
        .select("id, org_id, active")
        .eq("key_hash", key_hash)
        .eq("active", True)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy klucz API",
        )

    key = rows[0]
    # best-effort aktualizacja last_used_at
    service_client().table("api_keys").update(
        {"last_used_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", key["id"]).execute()

    return key["org_id"]
