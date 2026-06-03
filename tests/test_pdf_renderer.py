"""Testy renderu PDF faktury: kwota słownie, podsumowanie VAT, render HTML/PDF."""
from decimal import Decimal

import pytest

from core.pdf_renderer import (
    InvoicePdfData,
    amount_in_words,
    format_money,
    render_invoice_html,
    totals,
    vat_summary,
)

# Pozycje faktury ZAEL (kwiecień 2026, 177 kWh) — jak w test_billing_engine.
LINES = [
    {"label": "Opłata obrotowa", "quantity": "177", "unit": "kWh", "unit_price": "0.51760", "net_amount": "91.62", "vat_rate": "23", "sort_order": 1},
    {"label": "Opłata zmienna sieciowa", "quantity": "177", "unit": "kWh", "unit_price": "0.25660", "net_amount": "45.42", "vat_rate": "23", "sort_order": 2},
    {"label": "Opłata jakościowa", "quantity": "177", "unit": "kWh", "unit_price": "0.03320", "net_amount": "5.88", "vat_rate": "23", "sort_order": 3},
    {"label": "Opłata OZE", "quantity": "177", "unit": "kWh", "unit_price": "0.00730", "net_amount": "1.29", "vat_rate": "23", "sort_order": 4},
    {"label": "Opłata kogeneracyjna", "quantity": "177", "unit": "kWh", "unit_price": "0.00300", "net_amount": "0.53", "vat_rate": "23", "sort_order": 5},
    {"label": "Opłata mocowa", "quantity": "1", "unit": "mc", "unit_price": "17.18", "net_amount": "17.18", "vat_rate": "23", "sort_order": 6},
    {"label": "Abonament", "quantity": "1", "unit": "mc", "unit_price": "5.00", "net_amount": "5.00", "vat_rate": "23", "sort_order": 7},
    {"label": "Opłata stała sieciowa", "quantity": "1", "unit": "mc", "unit_price": "5.25", "net_amount": "5.25", "vat_rate": "23", "sort_order": 8},
]


def _data():
    return InvoicePdfData(
        invoice={
            "invoice_no": "FV/001/04/2026",
            "period_from": "2026-04-01",
            "period_to": "2026-04-30",
            "issued_date": "2026-05-01",
            "due_date": "2026-05-14",
            "kwh_consumed": "177.000",
            "is_estimated": False,
        },
        lines=LINES,
        organization={"name": "Zarządca Sp. z o.o.", "nip": "1234567890",
                      "address": "ul. Rynek 12, 00-001 Miasto", "bank_account": "PL00 1234 5678"},
        tenant={"name": "Najemca U1", "unit_no": "U1", "email": "u1@example.com", "nip": None},
        reading_start={"value_kwh": "1000.000", "read_type": "remote"},
        reading_end={"value_kwh": "1177.000", "read_type": "remote"},
        meter={"serial_no": "MB-0001", "label": "Lokal U1"},
    )


# --- amount_in_words --------------------------------------------------------
@pytest.mark.parametrize("value,expected", [
    ("0.00", "zero zł 00/100"),
    ("1.00", "jeden zł 00/100"),
    ("211.77", "dwieście jedenaście zł 77/100"),
    ("1000.50", "jeden tysiąc zł 50/100"),
    ("21.05", "dwadzieścia jeden zł 05/100"),
    ("15.00", "piętnaście zł 00/100"),
    ("2345.00", "dwa tysiące trzysta czterdzieści pięć zł 00/100"),
    ("1000000.00", "jeden milion zł 00/100"),
])
def test_amount_in_words(value, expected):
    assert amount_in_words(value) == expected


def test_amount_in_words_zaokraglenie():
    # 211.776 → 211,78
    assert amount_in_words("211.776").endswith("78/100")


# --- format_money -----------------------------------------------------------
def test_format_money_separatory():
    assert format_money("1234.5") == "1 234,50"
    assert format_money("211.77") == "211,77"


# --- vat_summary / totals ---------------------------------------------------
def test_vat_summary_pojedyncza_stawka():
    summary = vat_summary(LINES)
    assert len(summary) == 1
    row = summary[0]
    assert row["vat_rate"] == Decimal("23")
    assert row["net_amount"] == Decimal("172.17")
    # 172.17 * 23% = 39.5991 → 39.60; brutto 211.77 (zgodne ze spec ZAEL)
    assert row["vat_amount"] == Decimal("39.60")
    assert row["gross_amount"] == Decimal("211.77")


def test_vat_summary_wiele_stawek():
    lines = [
        {"net_amount": "100.00", "vat_rate": "23"},
        {"net_amount": "50.00", "vat_rate": "8"},
    ]
    summary = vat_summary(lines)
    assert [r["vat_rate"] for r in summary] == [Decimal("8"), Decimal("23")]
    assert summary[0]["vat_amount"] == Decimal("4.00")
    assert summary[1]["vat_amount"] == Decimal("23.00")


def test_totals_zgodne_z_zael():
    t = totals(LINES)
    assert t["net_amount"] == Decimal("172.17")
    assert t["gross_amount"] == Decimal("211.77")


# --- render HTML ------------------------------------------------------------
def test_render_html_zawiera_kluczowe_dane():
    html = render_invoice_html(_data())
    assert "FV/001/04/2026" in html
    assert "Najemca U1" in html
    assert "Opłata obrotowa" in html
    assert "211,77" in html              # brutto sformatowane
    assert "PL00 1234 5678" in html      # blok płatności
    assert "kwietnia 2026" in html       # miesiąc sprzedaży słownie
    assert "dwieście jedenaście" in html  # kwota słownie


def test_render_html_znacznik_szacowany():
    data = _data()
    data.invoice["is_estimated"] = True
    html = render_invoice_html(data)
    assert "szacowanym" in html.lower()


# --- render PDF (wymaga WeasyPrint + natywnych libów cairo/pango) ------------
def test_render_pdf_zwraca_pdf():
    # WeasyPrint na Windows bez GTK rzuca OSError przy ładowaniu libgobject —
    # pomijamy, gdy biblioteki natywne są niedostępne (CI/Docker je mają).
    try:
        from core.pdf_renderer import render_invoice_pdf
        pdf = render_invoice_pdf(_data())
    except (ImportError, OSError) as exc:
        pytest.skip(f"WeasyPrint/natywne biblioteki niedostępne: {exc}")
    assert pdf[:4] == b"%PDF"
