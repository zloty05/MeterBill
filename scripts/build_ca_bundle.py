"""Buduje certs/ca-bundle.pem: certifi + lokalne certy MITM-proxy (Windows).

Po co: na maszynach z antywirusem skanującym HTTPS (Norton, Kaspersky, ESET…)
albo z korporacyjnym proxy, ruch TLS jest przechwytywany i podpisywany lokalnym
certyfikatem root. Python nie ufa mu domyślnie → CERTIFICATE_VERIFY_FAILED przy
połączeniach do Supabase. Ten skrypt dokleja takie root-certy z magazynu Windows
do paczki certifi, dzięki czemu weryfikacja TLS znów działa (bez verify=False).

Bundle jest per-maszyna i NIE jest commitowany (.gitignore: certs/). Po
sklonowaniu repo na maszynie z MITM-proxy uruchom:

    .venv\\Scripts\\python.exe scripts\\build_ca_bundle.py

Na czystym środowisku (bez MITM) skrypt i tak zbuduje bundle = samo certifi,
co jest nieszkodliwe; core/ssl_setup.py użyje go tylko jeśli istnieje.

Wykrywane wystawcy proxy (po fragmencie nazwy, case-insensitive):
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import certifi

# Fragmenty nazw wystawców traktowane jako MITM-proxy do doklejenia.
PROXY_HINTS = ["norton", "kaspersky", "eset", "bitdefender", "avast", "fortinet", "zscaler"]

CERTS_DIR = Path(__file__).resolve().parent.parent / "certs"
BUNDLE = CERTS_DIR / "ca-bundle.pem"


def _export_proxy_certs_pem() -> list[str]:
    """Eksportuje pasujące root-certy z magazynu Windows do listy PEM-stringów."""
    hints = "','".join(PROXY_HINTS)
    ps = (
        "$h=@('" + hints + "');"
        "Get-ChildItem Cert:\\LocalMachine\\Root, Cert:\\CurrentUser\\Root -EA SilentlyContinue |"
        " Where-Object { $s=$_.Subject; $h | Where-Object { $s -match $_ } } |"
        " Sort-Object Thumbprint -Unique |"
        " ForEach-Object {"
        "   $b=[Convert]::ToBase64String($_.RawData,'InsertLineBreaks');"
        "   \"-----BEGIN CERTIFICATE-----`n$b`n-----END CERTIFICATE-----\""
        " }"
    )
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        print("Ostrzeżenie: nie udało się odczytać magazynu certów:", out.stderr.strip(), file=sys.stderr)
        return []
    blocks = [b.strip() for b in out.stdout.split("-----END CERTIFICATE-----") if "BEGIN CERTIFICATE" in b]
    return [b + "\n-----END CERTIFICATE-----" for b in blocks]


def main() -> None:
    CERTS_DIR.mkdir(exist_ok=True)
    base = Path(certifi.where()).read_text(encoding="utf-8").rstrip()

    proxy_pems = _export_proxy_certs_pem() if sys.platform == "win32" else []
    parts = [base, *[p.strip() for p in proxy_pems]]
    BUNDLE.write_text("\n".join(parts) + "\n", encoding="utf-8")

    print(f"Zapisano {BUNDLE}")
    print(f"  certifi CA + {len(proxy_pems)} cert(ów) proxy/antywirusa")
    if not proxy_pems and sys.platform == "win32":
        print("  (nie wykryto certów MITM — bundle = samo certifi)")


if __name__ == "__main__":
    main()
