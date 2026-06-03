"""Klienci Supabase.

- service_client(): działa na SERVICE_KEY, omija RLS. Używany przez backend
  do operacji systemowych (gateway readings, scheduler, generowanie faktur).
  Izolację org_id wymusza wtedy warstwa aplikacji (api/deps.py).
- anon_client(jwt): działa w kontekście zalogowanego usera (JWT z Supabase Auth),
  podlega politykom RLS. Używany dla operacji panelu zarządcy.
"""
from functools import lru_cache

from supabase import Client, create_client

from api.config import get_settings
from core.ssl_setup import configure_ssl

# Konfiguracja SSL pod MITM-proxy (Norton) musi zadziałać zanim powstanie
# pierwszy klient httpx. No-op na czystym środowisku (brak certs/ca-bundle.pem).
configure_ssl()


@lru_cache
def service_client() -> Client:
    """Klient z uprawnieniami serwisowymi (bypass RLS)."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


def anon_client(access_token: str | None = None) -> Client:
    """Klient w kontekście usera. Z access_token podlega RLS danego usera."""
    s = get_settings()
    client = create_client(s.supabase_url, s.supabase_anon_key)
    if access_token:
        client.postgrest.auth(access_token)
    return client
