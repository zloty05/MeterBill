# CLAUDE.md — EnergyBill / MeterBill

SaaS do automatycznego rozliczania energii elektrycznej między zarządcą budynku a najemcami.
Zastępuje ręczne odczyty M-Bus, Excel i wystawianie faktur. Język pracy: **polski**.
Właściciel zna PLC/automatykę (WAGO, Codesys, OPC UA, Docker), Pythona i Supabase, preferuje
plan przed implementacją — **przed każdym etapem przedstaw plan i poczekaj na akceptację.**

Pełna specyfikacja: [ENERGYBILL_MVP_PROMPT.md](ENERGYBILL_MVP_PROMPT.md) (schemat, taryfy,
fazy, decyzje biznesowe). Ten plik to mapa stanu kodu — przy rozbieżności źródłem prawdy jest kod.

## Architektura

```
[Liczniki M-Bus] → [Gateway lokalny] → [Cloud Backend (FastAPI)] → [Frontend React]
                                              ↓
                                    Supabase (Postgres + Auth + Storage)
```

- **Gateway** (faza 2, jeszcze nie w repo): lokalny skrypt Python na WAGO/RPi; wysyła tylko
  odczyty przez `POST /readings` z `X-API-Key`. Nie zna taryf ani logiki.
- **Backend**: FastAPI + Supabase (`supabase-py`), Celery+Redis (scheduler — jeszcze pusty),
  WeasyPrint (PDF — jeszcze nie napisane), Resend (email — jeszcze nie napisane).
- **Frontend** (faza 3, tylko design): React+Vite+Tailwind. Spec i design tokeny w
  [frontend/docs/README.md](frontend/docs/README.md). Brak kodu produkcyjnego.

## Układ kodu

```
api/
  main.py            # FastAPI app, montuje routery pod /api/v1, CORS, /health
  config.py          # Settings z .env (pydantic-settings), get_settings() z lru_cache
  deps.py            # autoryzacja: get_current_user/org (JWT), get_api_key_org (gateway)
  routers/           # jeden plik per zasób; większość endpointów to STUBY (NotImplementedError)
  schemas/invoices.py
core/                # czysta logika, bez zależności od web/HTTP
  billing_engine.py  # silnik taryfowy — czyste funkcje, ZERO I/O, w pełni testowalny
  invoice_service.py # orkiestracja: pobranie z Supabase + silnik + zapis (cała warstwa I/O)
  invoice_numbering.py # składanie FV/NNN/MM/YYYY; atomowość po stronie SQL (RPC)
  invoice_delivery.py # I/O dostarczania: render PDF + upload do Storage + wysyłka Resend
  pdf_renderer.py    # czysty render faktury (Jinja2+WeasyPrint), kwota słownie, VAT per stawka
  readings.py        # współdzielone: parse_date + latest_reading_at_or_before (odczyty graniczne)
  ssl_setup.py       # obejście MITM (Norton) — patrz niżej
templates/invoice.html # szablon faktury (HTML→PDF), CSS print inline, bez zewnętrznych fontów
db/supabase_client.py # service_client() (bypass RLS) i anon_client(jwt) (kontekst usera)
supabase/migrations/  # SQL: 001 schemat+RLS, 002 next_invoice_no(), 003 GRANT-y service_role
tasks/               # Celery — pusty placeholder (faza scheduler)
tests/               # pytest; fake_supabase.py = in-memory fake klienta (testy bez sieci)
```

## Stan implementacji (ważne — większość endpointów to stuby)

**Zaimplementowane i działające:**
- Schemat bazy + RLS + numeracja + GRANT-y (3 migracje).
- `core/billing_engine.py` — pełny silnik taryfowy z testami.
- `core/invoice_service.py` — generowanie faktur dla budynku (zapis do bazy, status `draft`).
- `core/invoice_numbering.py` + RPC `next_invoice_no`.
- `core/pdf_renderer.py` + `templates/invoice.html` — render faktury do PDF (kwota słownie,
  VAT per stawka). `core/invoice_delivery.py` — render→Storage→Resend (krok 6).
- `api/routers/invoices.py`: `POST /invoices/generate`, `GET /invoices`, `GET /invoices/{id}`,
  `GET /invoices/{id}/pdf`, `POST /invoices/{id}/send`, `PATCH /invoices/{id}/status`.
- Autoryzacja w `api/deps.py` (JWT i X-API-Key).

**Wymaga konfiguracji (poza kodem) zanim send/pdf zadziała na prod/dev:**
- Bucket Storage `invoices` (prywatny) — utwórz `python scripts/create_storage_bucket.py`
  (idempotentny; public=OFF, MIME=application/pdf). `invoice_delivery` tam archiwizuje PDF.
- `RESEND_API_KEY` + `FROM_EMAIL` w `.env` (bez nich `POST /send` zwraca 503).
- WeasyPrint wymaga natywnych libów (libcairo/pango); lokalnie na Windows bez GTK render PDF
  nie działa (test renderu jest pod skip) — w Dockerze wg `ENERGYBILL_MVP_PROMPT.md` l. 619.

**Stuby (`raise NotImplementedError`) — do zrobienia w kolejnych krokach:**
- Routery `buildings, meters, readings, tenants, tariffs, organizations, portal`.
- `POST /readings` (gateway).
- Celery scheduler, gateway agent.

Przed twierdzeniem „endpoint X działa" sprawdź, czy ciało nie jest `NotImplementedError`.

## Konwencje (trzymaj się ich)

- **Pieniądze = `Decimal`, nigdy `float`.** Konwersja przez `str()`. Zaokrąglenie groszy:
  `ROUND_HALF_UP` do `0.01`. VAT liczony per stawka (grupowanie netto po `vat_rate`), nie per pozycja.
- **Silnik (`billing_engine`) nie robi I/O.** Dostaje dane jako dataclasy, zwraca `InvoiceResult`.
  Pobieranie/zapis żyje w `invoice_service`. Nie wciągaj zapytań Supabase do silnika.
- **Izolacja multi-tenant (hybryda):** backend działa na `SERVICE_KEY` → omija RLS, więc
  **każde zapytanie musi filtrować po `org_id`** pobranym z `get_current_org`/`get_api_key_org`.
  RLS w bazie to druga warstwa (działa dla anon/authenticated z JWT). Nie polegaj wyłącznie na RLS.
- **Dwa tory auth:** panel/portal → JWT Bearer (Supabase, HS256, audience `authenticated`);
  gateway → `X-API-Key` (sha256 hash w `api_keys`). Portal najemcy → token w URL (faza 4).
- **Numery faktur** rezerwuj przez RPC `next_invoice_no` (atomowy upsert), nie licz w aplikacji.
- **Idempotencja odczytów:** `UNIQUE(meter_id, read_at)` w `readings`.
- **Pominięcia przy generowaniu:** najemca bez kompletu danych (odczyt/przypisanie/taryfa) lub
  z duplikatem faktury trafia do `skipped`, nie blokuje pozostałych. Nie szacujemy automatycznie.
- Komentarze i komunikaty błędów po polsku, zgodnie z istniejącym kodem.

## Środowisko — pułapki (nieoczywiste!)

- **Python 3.14** lokalnie. Część wersji w `requirements.txt` jest podniesiona względem promptu
  (3.12), bo natywne paczki (pydantic-core, cryptography) potrzebują wheeli cp314. `supabase`
  **przypięty na 2.5.0** — nowsze ciągną `pyiceberg` (brak koła cp314, wymaga MSVC). Nie podbijaj
  bez sprawdzenia, że instalacja przechodzi.
- **Norton MITM / SSL:** maszyna dev skanuje HTTPS i podstawia własny root cert → Python
  rzuca `CERTIFICATE_VERIFY_FAILED`. `core/ssl_setup.py` (wołane przy starcie `supabase_client`)
  jest **no-op, dopóki nie istnieje `certs/ca-bundle.pem`**. Wygeneruj bundle:
  `python scripts/build_ca_bundle.py`. To NIE jest `verify=False` — łagodzi tylko
  `VERIFY_X509_STRICT`, pełna weryfikacja łańcucha i hosta zostaje. Na CI/prod bez MITM nieaktywne.
  `ssl_setup` łata **dwa tory niezależnie**: httpx (Supabase) przez `ssl.create_default_context`
  oraz urllib3/`requests` (klient Resend) przez `create_urllib3_context` w `util.ssl_` **i**
  `urllib3.connection`. Resend domyślnie używa `requests`, więc bez patcha urllib3 `POST /send`
  padał pod Nortonem mimo działającego bundla.

## Komendy

```powershell
# Testy (czysta logika, bez sieci — używa fake_supabase)
python -m pytest

# Lokalny serwer API
uvicorn api.main:app --reload          # http://localhost:8000, docs /docs, /health

# Cały stack (api + worker + redis + frontend)
docker compose up

# Migracje: aplikowane przez Supabase CLI lub wklejane w SQL editor; pliki w supabase/migrations/
```

## Zakres / fazy

Krok 1–3: schemat, FastAPI boilerplate, auth. Krok 4–5 (zrobione): silnik taryfowy +
generowanie faktur + setup Supabase. Dalej: PDF (WeasyPrint), email (Resend), Celery scheduler,
implementacja stubów CRUD, gateway agent, frontend, portal najemcy.

**Decyzja MVP:** płatności oznaczane ręcznie przez zarządcę (brak integracji bankowej).
System jest narzędziem, nie doradcą podatkowym — odpowiedzialność za zgodność taryf/faktur
z prawem leży po stronie zarządcy (patrz spec).
