"""Testy numeracji faktur (core/invoice_numbering)."""
from datetime import date

import pytest

from core.invoice_numbering import format_invoice_no, next_invoice_no


def test_format_zero_padded():
    assert format_invoice_no(1, date(2026, 4, 15)) == "FV/001/04/2026"
    assert format_invoice_no(42, date(2026, 12, 1)) == "FV/042/12/2026"
    assert format_invoice_no(7, date(2026, 1, 31)) == "FV/007/01/2026"


def test_format_three_digit_keeps_width():
    assert format_invoice_no(123, date(2026, 5, 1)) == "FV/123/05/2026"


class _FakeRpc:
    """Naśladuje client.rpc(...).execute() z licznikiem per (org, year, month)."""

    def __init__(self, store):
        self.store = store
        self._args = None

    def rpc(self, name, params):
        assert name == "next_invoice_no"
        self._args = params
        return self

    def execute(self):
        p = self._args
        key = (p["p_org_id"], p["p_year"], p["p_month"])
        self.store[key] = self.store.get(key, 0) + 1
        return type("R", (), {"data": self.store[key]})()


def test_next_invoice_no_increments_per_month():
    client = _FakeRpc({})
    org = "org-1"
    apr = date(2026, 4, 10)

    assert next_invoice_no(client, org, apr) == "FV/001/04/2026"
    assert next_invoice_no(client, org, apr) == "FV/002/04/2026"
    assert next_invoice_no(client, org, date(2026, 4, 28)) == "FV/003/04/2026"


def test_next_invoice_no_resets_in_new_month():
    client = _FakeRpc({})
    org = "org-1"

    assert next_invoice_no(client, org, date(2026, 4, 1)) == "FV/001/04/2026"
    # nowy miesiąc → licznik startuje od 1
    assert next_invoice_no(client, org, date(2026, 5, 1)) == "FV/001/05/2026"


def test_next_invoice_no_independent_per_org():
    client = _FakeRpc({})
    apr = date(2026, 4, 1)

    assert next_invoice_no(client, "org-a", apr) == "FV/001/04/2026"
    assert next_invoice_no(client, "org-b", apr) == "FV/001/04/2026"


def test_next_invoice_no_raises_when_rpc_returns_none():
    class _NullRpc:
        def rpc(self, name, params):
            return self

        def execute(self):
            return type("R", (), {"data": None})()

    with pytest.raises(RuntimeError):
        next_invoice_no(_NullRpc(), "org", date(2026, 4, 1))
