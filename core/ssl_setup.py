"""Konfiguracja SSL dla środowisk z przechwytywaniem TLS (antywirus/proxy).

Problem: na maszynie dev Norton Antivirus skanuje HTTPS ("SSL/TLS scanning"),
podstawiając własny certyfikat root. Python/httpx nie ufa mu domyślnie, więc
połączenia do Supabase padają na CERTIFICATE_VERIFY_FAILED. Dodatkowo cert
Nortona ma Basic Constraints nieoznaczone jako krytyczne, co OpenSSL 3.x
(Python 3.14) odrzuca przy domyślnej fladze VERIFY_X509_STRICT.

Rozwiązanie (idempotentne, wołać raz przy starcie procesu przed utworzeniem
klienta Supabase):
  1. Wskaż httpx/requests kombinowany bundle CA (certifi + cert Nortona) przez
     SSL_CERT_FILE / REQUESTS_CA_BUNDLE — o ile plik istnieje.
  2. Złagodź VERIFY_X509_STRICT w domyślnym kontekście SSL (httpx tworzy własny
     kontekst przez ssl.create_default_context — patchujemy tę funkcję).

Aktywne tylko gdy istnieje certs/ca-bundle.pem (środowisko dev z Nortonem).
Na czystym środowisku (CI, prod bez MITM) moduł jest no-op — weryfikacja TLS
działa normalnie i rygorystycznie.

UWAGA: złagodzenie strict dotyczy wyłącznie rozszerzenia Basic-Constraints-
critical; pełna weryfikacja łańcucha i hosta nadal obowiązuje. To NIE jest
verify=False.
"""
from __future__ import annotations

import os
import ssl
from pathlib import Path

_BUNDLE = Path(__file__).resolve().parent.parent / "certs" / "ca-bundle.pem"
_applied = False


def configure_ssl() -> bool:
    """Konfiguruje SSL pod MITM-proxy, jeśli obecny jest lokalny bundle CA.

    Zwraca True gdy zastosowano obejście, False gdy pominięto (brak bundla).
    Idempotentne — kolejne wywołania nie robią nic.
    """
    global _applied
    if _applied:
        return True
    if not _BUNDLE.exists():
        return False

    bundle = str(_BUNDLE)
    os.environ.setdefault("SSL_CERT_FILE", bundle)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)

    _orig = ssl.create_default_context

    def _patched(*args, **kwargs):
        ctx = _orig(*args, **kwargs)
        # cafile może być już podany przez wołającego; jeśli nie — użyj bundla
        if not kwargs.get("cafile") and not kwargs.get("capath") and not kwargs.get("cadata"):
            try:
                ctx.load_verify_locations(cafile=bundle)
            except Exception:
                pass
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        return ctx

    _patched._meterbill_patched = True  # marker idempotencji
    if not getattr(ssl.create_default_context, "_meterbill_patched", False):
        ssl.create_default_context = _patched

    _applied = True
    return True
