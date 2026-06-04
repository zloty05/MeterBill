"""Testy symulatora PLC (gateway/plc_simulator.py).

Sprawdzają, że symulator buduje poprawny payload i wysyła X-API-Key oraz że
ponawia wysyłkę przy błędzie sieci (jak powinien robić sterownik przy braku 4G).
requests.post jest mockowany — bez realnej sieci.
"""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gateway import plc_simulator


M1 = "d1111111-1111-4111-8111-111111111111"


def test_read_meter_payload_shape():
    payload = plc_simulator.read_meter({"meter_id": M1, "base_kwh": 1000.0})
    assert payload["meter_id"] == M1
    assert payload["value_kwh"] >= 1000.0  # narasta od base
    assert payload["read_type"] == "remote"
    assert payload["source"] == "plc-simulator"
    assert "read_at" not in payload  # czas nadaje serwer


def test_post_reading_sends_api_key(monkeypatch):
    captured = {}

    class _Resp:
        status_code = 201
        text = ""

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return _Resp()

    monkeypatch.setattr(plc_simulator.requests, "post", fake_post)
    ok = plc_simulator.post_reading(
        "http://x/readings", "klucz-abc", {"meter_id": M1, "value_kwh": 1.0}
    )
    assert ok is True
    assert captured["headers"]["X-API-Key"] == "klucz-abc"
    assert captured["json"]["meter_id"] == M1


def test_post_reading_200_is_success(monkeypatch):
    """Duplikat (200) traktujemy jako sukces — nie ponawiamy."""

    class _Resp:
        status_code = 200
        text = ""

    monkeypatch.setattr(plc_simulator.requests, "post", lambda *a, **k: _Resp())
    assert plc_simulator.post_reading("http://x", "k", {"meter_id": M1, "value_kwh": 1.0})


def test_post_reading_4xx_no_retry(monkeypatch):
    """401/404 to błąd trwały — zwróć False, nie ponawiaj."""
    calls = {"n": 0}

    class _Resp:
        status_code = 401
        text = "zły klucz"

    def fake_post(*a, **k):
        calls["n"] += 1
        return _Resp()

    monkeypatch.setattr(plc_simulator.requests, "post", fake_post)
    ok = plc_simulator.post_reading("http://x", "k", {"meter_id": M1, "value_kwh": 1.0})
    assert ok is False
    assert calls["n"] == 1  # bez ponawiania


def test_post_reading_retries_on_network_error(monkeypatch):
    """Wyjątek sieci → ponawiamy; po wyczerpaniu prób False (bez realnego sleep)."""
    calls = {"n": 0}

    def fake_post(*a, **k):
        calls["n"] += 1
        raise requests.ConnectionError("brak 4G")

    monkeypatch.setattr(plc_simulator.requests, "post", fake_post)
    monkeypatch.setattr(plc_simulator.time, "sleep", lambda *_: None)
    ok = plc_simulator.post_reading(
        "http://x", "k", {"meter_id": M1, "value_kwh": 1.0}, retries=3, backoff=0.0
    )
    assert ok is False
    assert calls["n"] == 3
