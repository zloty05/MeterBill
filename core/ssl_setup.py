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

    _patch_urllib3(bundle)

    _applied = True
    return True


def _patch_urllib3(bundle: str) -> None:
    """Łagodzi VERIFY_X509_STRICT także w torze urllib3 (requests).

    httpx tworzy kontekst przez ssl.create_default_context (łapany wyżej), ale
    urllib3 — używany przez `requests`, a więc i przez klienta Resend — buduje
    kontekst własną funkcją create_urllib3_context, która na Python 3.13+ sama
    dokłada VERIFY_X509_STRICT. Bez tego patcha POST /invoices/{id}/send pada na
    maszynie dev z Nortonem (cert MITM ma Basic-Constraints nie-critical).

    Jak wyżej: czyścimy wyłącznie flagę strict i dokładamy bundle CA; pełna
    weryfikacja łańcucha i hosta zostaje. No-op gdy urllib3 nieobecny.
    """
    try:
        import urllib3.util.ssl_ as u3ssl
    except Exception:
        return

    if getattr(u3ssl.create_urllib3_context, "_meterbill_patched", False):
        return

    _orig_u3 = u3ssl.create_urllib3_context

    def _patched_u3(*args, **kwargs):
        ctx = _orig_u3(*args, **kwargs)
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        try:
            ctx.load_verify_locations(cafile=bundle)
        except Exception:
            pass
        return ctx

    _patched_u3._meterbill_patched = True
    u3ssl.create_urllib3_context = _patched_u3

    # urllib3.connection importuje create_urllib3_context do własnej przestrzeni
    # nazw (`from .util.ssl_ import ...`) — podmiana atrybutu w util.ssl_ nie
    # wpływa na tę referencję, więc patchujemy ją osobno. To ona jest używana
    # przy faktycznym połączeniu (HTTPSConnection.connect, ssl_context=None).
    try:
        import urllib3.connection as u3conn
        if not getattr(u3conn.create_urllib3_context, "_meterbill_patched", False):
            u3conn.create_urllib3_context = _patched_u3
    except Exception:
        pass
