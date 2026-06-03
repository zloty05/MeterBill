"""Testy dostarczania faktur (core/invoice_delivery): Storage + Resend na fake kliencie.

Render PDF i Resend są mockowane — nie chcemy zależeć od natywnego WeasyPrint
ani od sieci. Sprawdzamy orkiestrację: pdf_path, issued_date, status/sent_at,
filtr org_id i mapowanie błędów.
"""
from datetime import date
from types import SimpleNamespace

import pytest

import core.invoice_delivery as delivery
from core.invoice_delivery import (
    InvoiceNotFound,
    ResendNotConfigured,
    get_or_build_pdf,
    send_invoice_email,
)
from tests.fake_supabase import FakeSupabase

ORG = "org-1"
TENANT = "ten-1"
INVOICE = "inv-1"
METER = "mtr-1"


def base_db(**overrides):
    data = {
        "invoices": [{
            "id": INVOICE, "org_id": ORG, "tenant_id": TENANT,
            "invoice_no": "FV/001/04/2026",
            "period_from": "2026-04-01", "period_to": "2026-04-30",
            "issued_date": None, "pdf_path": None,
            "kwh_consumed": "177.000", "status": "draft",
            "due_date": "2026-05-14", "gross_amount": "211.77", "is_estimated": False,
        }],
        "invoice_lines": [
            {"id": "l1", "invoice_id": INVOICE, "label": "Opłata obrotowa",
             "quantity": "177", "unit": "kWh", "unit_price": "0.51760",
             "net_amount": "172.17", "vat_rate": "23", "sort_order": 1},
        ],
        "organizations": [{"id": ORG, "name": "Zarządca", "nip": "123",
                           "address": "ul. Rynek 1", "bank_account": "PL00 1111"}],
        "tenants": [{"id": TENANT, "name": "Najemca U1", "email": "u1@example.com",
                     "nip": None, "unit_no": "U1", "building_id": "bld-1"}],
        "meter_assignments": [{"id": "a1", "tenant_id": TENANT, "meter_id": METER,
                               "valid_from": "2026-01-01", "valid_to": None}],
        "meters": [{"id": METER, "serial_no": "MB-1", "label": "U1"}],
        "readings": [
            {"id": "r1", "meter_id": METER, "read_at": "2026-04-01T00:00:00",
             "value_kwh": "1000.000", "read_type": "remote", "is_estimated": False},
            {"id": "r2", "meter_id": METER, "read_at": "2026-04-30T23:00:00",
             "value_kwh": "1177.000", "read_type": "remote", "is_estimated": False},
        ],
    }
    data.update(overrides)
    return data


@pytest.fixture
def fake_pdf(monkeypatch):
    """Mockuje render PDF, by nie wymagać natywnego WeasyPrint."""
    monkeypatch.setattr(delivery, "render_invoice_pdf", lambda data: b"%PDF-fake")
    return b"%PDF-fake"


# --- get_or_build_pdf -------------------------------------------------------
def test_build_pdf_zapisuje_path_i_issued_date(fake_pdf):
    db = base_db()
    client = FakeSupabase(db)
    pdf, path = get_or_build_pdf(client, ORG, INVOICE)

    assert pdf == b"%PDF-fake"
    assert path == f"{ORG}/2026/FV-001-04-2026.pdf"
    inv = db["invoices"][0]
    assert inv["pdf_path"] == path
    assert inv["issued_date"] == date.today().isoformat()
    # plik trafił do bucketu invoices
    assert path in client.storage.buckets["invoices"]


def test_build_pdf_nieistniejaca_faktura(fake_pdf):
    client = FakeSupabase(base_db())
    with pytest.raises(InvoiceNotFound):
        get_or_build_pdf(client, ORG, "nie-ma")


def test_build_pdf_izolacja_org(fake_pdf):
    client = FakeSupabase(base_db())
    with pytest.raises(InvoiceNotFound):
        get_or_build_pdf(client, "inna-org", INVOICE)


# --- send_invoice_email -----------------------------------------------------
def _settings(**kw):
    base = {"resend_api_key": "re_test", "from_email": "faktury@x.pl"}
    base.update(kw)
    return SimpleNamespace(**base)


def test_send_oznacza_sent_i_zwraca_email_id(fake_pdf, monkeypatch):
    sent_calls = {}

    def fake_send(params):
        sent_calls["params"] = params
        return {"id": "email-123"}

    fake_resend = SimpleNamespace(
        api_key=None,
        Emails=SimpleNamespace(send=fake_send, SendParams=dict),
    )
    monkeypatch.setitem(__import__("sys").modules, "resend", fake_resend)

    db = base_db()
    client = FakeSupabase(db)
    result = send_invoice_email(client, ORG, INVOICE, _settings())

    assert result["status"] == "sent"
    assert result["email_id"] == "email-123"
    assert db["invoices"][0]["status"] == "sent"
    assert db["invoices"][0]["sent_at"]
    # załącznik PDF i adresat
    assert sent_calls["params"]["to"] == ["u1@example.com"]
    assert sent_calls["params"]["attachments"][0]["filename"] == "FV-001-04-2026.pdf"
    # blok płatności w treści
    assert "PL00 1111" in sent_calls["params"]["html"]


def test_send_bez_konfiguracji_resend(fake_pdf):
    client = FakeSupabase(base_db())
    with pytest.raises(ResendNotConfigured):
        send_invoice_email(client, ORG, INVOICE, _settings(resend_api_key=""))
    with pytest.raises(ResendNotConfigured):
        send_invoice_email(client, ORG, INVOICE, _settings(from_email=""))


def test_send_najemca_bez_emaila(fake_pdf, monkeypatch):
    monkeypatch.setitem(
        __import__("sys").modules, "resend",
        SimpleNamespace(api_key=None, Emails=SimpleNamespace(send=lambda p: {"id": "x"}, SendParams=dict)),
    )
    db = base_db()
    db["tenants"][0]["email"] = None
    client = FakeSupabase(db)
    with pytest.raises(InvoiceNotFound):
        send_invoice_email(client, ORG, INVOICE, _settings())
