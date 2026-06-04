# Gateway — przyjmowanie odczytów liczników

Warstwa, która dostarcza odczyty z liczników do chmury przez `POST /readings`.

## Architektura (MVP)

```
[Liczniki M-Bus/Modbus] → [WAGO 750-8217 (PFC200 + modem 4G)] ──HTTPS──→ [Chmura: FastAPI]
                                                              POST /readings
                                                              X-API-Key
```

Sterownik WAGO odczytuje liczniki (program Codesys, dowolny protokół) i **sam**
wysyła odczyty do chmury przez własne łącze 4G. Nie ma osobnego pośrednika
(RPi/serwer) — 750-8217 ma wbudowany modem, więc dodatkowe urządzenie byłoby
zbędnym kosztem i punktem awarii.

Backend jest **vendor-agnostic**: nie zna protokołu licznika ani taryf. Przyjmuje
tylko odczyty. Dlatego gdyby u jakiegoś klienta sterownik nie miał dostępu do
internetu (zamknięta sieć OT), można wstawić dowolnego pośrednika mówiącego tym
samym kontraktem — endpoint się nie zmienia.

## Kontrakt `POST /readings`

- **URL:** `{API}/api/v1/readings` (np. `https://api.energybill.pl/api/v1/readings`)
- **Nagłówki:**
  - `X-API-Key: <klucz>` — wygeneruj przez `python scripts/make_api_key.py`
  - `Content-Type: application/json`
- **Body (jeden odczyt na request):**

```json
{
  "meter_id": "uuid-licznika-z-bazy",
  "value_kwh": 1234.567,
  "power_kw": 3.2,
  "read_type": "remote",
  "source": "wago-pfc200"
}
```

Pola:

| Pole | Wymagane | Uwagi |
|---|---|---|
| `meter_id` | tak | UUID licznika; musi należeć do organizacji klucza |
| `value_kwh` | tak | liczba ≥ 0 (stan licznika narastający, nie zużycie) |
| `power_kw` | nie | moc chwilowa, jeśli licznik ją podaje |
| `read_type` | nie | `remote` (domyślnie) \| `physical` \| `estimated` |
| `is_estimated` | nie | `false` domyślnie |
| `source` | nie | etykieta źródła, np. `wago-pfc200`; domyślnie `plc` |
| `read_at` | nie | **pomiń** — czas nadaje serwer (sterownik nie musi mieć NTP) |

- **Odpowiedzi:**

| Kod | Znaczenie | Reakcja gatewaya |
|---|---|---|
| `201` | odczyt zapisany | OK |
| `200` | duplikat `(meter_id, read_at)` — idempotencja | OK, nie ponawiaj |
| `401` | brak/zły `X-API-Key` | błąd trwały — alarm, nie ponawiaj |
| `404` | `meter_id` nie istnieje lub spoza organizacji | błąd trwały — alarm |
| `422` | błędne body (np. `value_kwh` ujemne) | błąd trwały — alarm |
| `5xx`/timeout | problem chmury/łącza | **ponów** z backoff, buforuj lokalnie |

### Idempotencja

Baza ma `UNIQUE(meter_id, read_at)`. Ponowienie tego samego odczytu (np. retry po
zerwanym 4G) zwróci `200` z istniejącym wpisem, bez duplikatu. Bezpiecznie więc
ponawiać do skutku.

### Bufor offline

Gdy 4G padnie, sterownik powinien **buforować odczyty lokalnie** (pamięć
nieulotna / karta) i wysłać je po odzyskaniu łącza — inaczej zgubisz odczyty z
okna awarii. Dzięki idempotencji można bezpiecznie wysłać cały bufor.

### Rotacja klucza

Klucz to plaintext widoczny tylko przy generowaniu (w bazie jest sha256). Aby
rotować: wygeneruj nowy (`make_api_key.py`), wgraj do sterownika, stary
dezaktywuj (`api_keys.active = false`).

## Pliki w tym katalogu

- **`plc_post_readings.st`** — szkic referencyjny Codesys ST: budowa JSON, nagłówek
  `X-API-Key`, zarys retry/bufora. Do dostosowania pod Twoje firmware/biblioteki.
- **`plc_simulator.py`** — symulator PLC w Pythonie. Testuje `POST /readings`
  end-to-end **bez sterownika** (przydatne w developmencie).
- **`config.example.yaml`** — przykład configu symulatora (skopiuj do `config.yaml`).
- **`requirements.txt`** — zależności symulatora (tylko dla niego, nie dla WAGO).

## Test end-to-end bez sterownika (symulator)

```powershell
# 1. Uruchom backend
uvicorn api.main:app --reload

# 2. Wygeneruj klucz API (wypisze plaintext — skopiuj)
python scripts/make_api_key.py

# 3. Skonfiguruj symulator
#    skopiuj gateway/config.example.yaml -> gateway/config.yaml
#    wstaw api_key (z kroku 2) i meter_id (UUID licznika z bazy / seed)
pip install -r gateway/requirements.txt

# 4. Wyślij jeden cykl odczytów
python gateway/plc_simulator.py --config gateway/config.yaml --once
```
