"""Numeracja faktur: FV/NNN/MM/YYYY, sekwencyjna per organizacja per miesiąc.

Atomowy increment realizuje funkcja SQL `next_invoice_no`
(supabase/migrations/..._invoice_numbering.sql), wołana przez RPC.
Aplikacja tylko składa string.
Trzymanie inkrementu w bazie zapobiega duplikatom numerów przy współbieżnym
generowaniu (ENERGYBILL_MVP_PROMPT.md l. 606-607).
"""
from __future__ import annotations

from datetime import date


def format_invoice_no(seq_no: int, period: date) -> str:
    """Składa numer FV/NNN/MM/YYYY z numeru porządkowego i daty okresu."""
    return f"FV/{seq_no:03d}/{period.month:02d}/{period.year}"


def next_invoice_no(client, org_id: str, period_from: date) -> str:
    """Rezerwuje kolejny numer faktury dla org w miesiącu period_from.

    Woła funkcję SQL next_invoice_no(p_org_id, p_year, p_month) przez RPC —
    atomowy increment w invoice_sequences. Zwraca gotowy string FV/NNN/MM/YYYY.
    """
    res = client.rpc(
        "next_invoice_no",
        {
            "p_org_id": org_id,
            "p_year": period_from.year,
            "p_month": period_from.month,
        },
    ).execute()

    seq_no = res.data
    if seq_no is None:
        raise RuntimeError("next_invoice_no RPC nie zwróciło numeru")

    return format_invoice_no(int(seq_no), period_from)
