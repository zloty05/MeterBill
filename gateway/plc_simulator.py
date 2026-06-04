"""Symulator PLC — wysyła odczyty do POST /readings tak, jak zrobi to sterownik.

Nie jest to produkcyjny gateway. Produkcyjnie odczyty wysyła WAGO 750-8217
(PFC200 z modemem 4G) bezpośrednio z programu Codesys — patrz README.md i
plc_post_readings.st. Ten skrypt służy do testów end-to-end backendu BEZ
sterownika: czyta listę liczników z configu, generuje narastające kWh i woła
endpoint z nagłówkiem X-API-Key, z prostym retry/backoff (jak powinien robić PLC
przy chwilowym braku 4G).

Użycie:
  python gateway/plc_simulator.py --config gateway/config.example.yaml
  python gateway/plc_simulator.py --config gateway/config.example.yaml --once
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import requests
import yaml


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_meter(meter: dict) -> dict:
    """Symuluje odczyt jednego licznika.

    PLC dostarczyłby realną wartość kWh z licznika; tu dokładamy losowy przyrost
    do wartości bazowej, by kolejne odczyty narastały (jak prawdziwy licznik).
    """
    base = float(meter.get("base_kwh", 1000.0))
    drift = random.uniform(0.5, 3.0)
    return {
        "meter_id": meter["meter_id"],
        "value_kwh": round(base + drift, 3),
        "read_type": "remote",
        "source": "plc-simulator",
    }


def post_reading(
    api_url: str, api_key: str, payload: dict, *, retries: int = 3, backoff: float = 2.0
) -> bool:
    """Wysyła jeden odczyt. Zwraca True przy sukcesie (201/200).

    Retry/backoff odwzorowuje to, co PLC powinien robić przy zerwanym 4G:
    ponawiać, a nie gubić odczyt. Realny gateway dodatkowo buforuje odczyty
    lokalnie — patrz README.
    """
    headers = {"X-API-Key": api_key}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                state = "duplikat (200)" if resp.status_code == 200 else "zapisano (201)"
                print(f"  {payload['meter_id']}: {state}")
                return True
            print(
                f"  {payload['meter_id']}: błąd {resp.status_code} — {resp.text[:200]}"
            )
            return False  # 4xx nie ma sensu ponawiać (zły klucz / zły meter)
        except requests.RequestException as exc:
            wait = backoff * attempt
            print(f"  {payload['meter_id']}: sieć padła ({exc}); retry za {wait:.0f}s")
            time.sleep(wait)
    print(f"  {payload['meter_id']}: nie udało się wysłać po {retries} próbach")
    return False


def run_cycle(cfg: dict) -> None:
    print("Cykl odczytu:")
    for meter in cfg["meters"]:
        payload = read_meter(meter)
        post_reading(cfg["api_url"], cfg["api_key"], payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Symulator PLC dla POST /readings.")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config.example.yaml")),
        help="Ścieżka do pliku konfiguracji YAML.",
    )
    parser.add_argument("--once", action="store_true", help="Jeden cykl i koniec.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    interval = int(cfg.get("interval_seconds", 900))

    if args.once:
        run_cycle(cfg)
        return 0

    print(f"Start symulatora; interwał {interval}s (Ctrl+C kończy).")
    try:
        while True:
            run_cycle(cfg)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nZatrzymano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
