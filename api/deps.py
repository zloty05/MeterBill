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
from dataclasses import dataclass
from datetime import datetime, timezone

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


def _decode_jwt(token: str) -> dict:
    s = get_settings()
    try:
        # Supabase podpisuje JWT sekretem HS256; audience = "authenticated"
        return jwt.decode(
            token,
            s.supabase_jwt_secret,
            algorithms=["HS256"],
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
