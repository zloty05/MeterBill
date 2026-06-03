# EnergyBill SaaS – Prompt startowy MVP dla Claude Code

## Kontekst i cel

Buduję SaaS do automatycznego rozliczania energii elektrycznej między zarządcą budynku
a jego najemcami. System ma zastąpić ręczne odczyty liczników, Excel i ręczne wystawianie
faktur. Jestem doświadczonym programistą PLC/automatyki (WAGO, Codesys, OPC UA, Docker),
znam Pythona i mam doświadczenie z Supabase. Preferuję planowanie przed implementacją.

Prowadź rozmowę po polsku. Przed każdym etapem implementacji przedstaw plan i czekaj
na moją akceptację.

---

## Problem który rozwiązujemy

Zarządca budynku (np. kamienica z lokalami usługowymi i mieszkaniami) płaci jeden rachunek
zbiorczy do dystrybutora energii (np. ZAEL-Energo, taryfa G11). W budynku są podliczniki
M-Bus na każdy lokal. Dziś zarządca:

1. Jeździ osobiście i zapisuje odczyty na kartce
2. Ręcznie liczy rozliczenie w Excelu
3. Nie wie jak podzielić opłaty stałe (opłata mocowa, abonament, sieć stała)
4. Ręcznie wystawia faktury VAT lub rachunki w programie FK
5. Ręcznie wysyła emaile z PDF do każdego najemcy
6. Ręcznie śledzi kto zapłacił

Koszt: 8–12 h pracy miesięcznie na jeden budynek. Przy 4 budynkach = ~640–960 zł/mc strat.

---

## Architektura systemu (zatwierdzona)

### Warstwy

```
[Liczniki M-Bus] → [Gateway lokalny] → [Cloud Backend] → [Frontend]
```

**Gateway lokalny (u klienta):**
- WAGO PFC300 z Codesys / Raspberry Pi + konwerter USB-MBus / dowolny konwerter IP
- Agent lokalny: skrypt Python który czyta liczniki i wysyła POST do API
- Gateway jest vendor-agnostic – wysyła tylko odczyty przez HTTPS REST
- Nie zna taryf ani logiki fakturowania

**Cloud Backend (nasz serwer):**
- FastAPI (Python) – REST API, JWT auth, multi-tenant
- Supabase (PostgreSQL) – baza danych, auth, storage
- Celery + Redis – scheduler miesięczny, kolejka zadań async
- WeasyPrint – generowanie PDF faktur
- Resend.com – wysyłka emaili z PDF

**Frontend:**
- React (Vite) + Tailwind CSS
- Supabase JS client
- Dwa widoki: panel zarządcy + portal najemcy (link jednorazowy z tokenem)

**Hosting:**
- Docker Compose (jeden plik, VPS lub Railway/Render)
- Supabase cloud (managed)

---

## Schemat bazy danych (zatwierdzony)

### Encje i relacje

```
organizations ||--o{ buildings : owns
organizations ||--o{ users : has
buildings ||--o{ meters : contains
buildings ||--o{ tenants : has
meters ||--o{ readings : produces
meters }o--|| tariff_templates : uses
tenants ||--o{ meter_assignments : has
meters ||--o{ meter_assignments : assigned_via
tenants ||--o{ invoices : receives
invoices ||--o{ invoice_lines : contains
tariff_templates ||--o{ tariff_components : has
```

### Tabele SQL (PostgreSQL / Supabase)

```sql
-- Multi-tenancy: każdy zarządca = osobna organizacja
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  nip TEXT,
  plan TEXT DEFAULT 'free', -- free | pro | enterprise
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Budynki zarządcy
CREATE TABLE buildings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  main_meter_ppe TEXT -- kod PPE licznika głównego od dystrybutora
);

-- Użytkownicy (zarządcy)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  role TEXT DEFAULT 'admin', -- admin | viewer
  active BOOLEAN DEFAULT true
);

-- Podliczniki w budynku
CREATE TABLE meters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
  tariff_id UUID REFERENCES tariff_templates(id),
  serial_no TEXT NOT NULL,
  mbus_address TEXT, -- adres M-Bus (hex, np. "05")
  protocol TEXT DEFAULT 'mbus', -- mbus | modbus | opcua | manual
  ppe_code TEXT,
  tariff_group TEXT DEFAULT 'G11', -- G11 | G12
  label TEXT -- np. "Lokal U1 – parter"
);

-- Najemcy
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  nip TEXT, -- jeśli firma – faktura VAT; jeśli puste – rachunek
  unit_no TEXT NOT NULL, -- nr lokalu np. "U1", "M3"
  active BOOLEAN DEFAULT true,
  portal_token TEXT UNIQUE -- jednorazowy token do portalu (UUID)
);

-- Przypisanie licznika do najemcy (z historią)
CREATE TABLE meter_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id),
  meter_id UUID REFERENCES meters(id),
  valid_from DATE NOT NULL,
  valid_to DATE -- NULL = aktywne
);

-- Odczyty liczników
CREATE TABLE readings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meter_id UUID REFERENCES meters(id) ON DELETE CASCADE,
  read_at TIMESTAMPTZ NOT NULL,
  read_type TEXT DEFAULT 'remote', -- remote | physical | estimated
  value_kwh NUMERIC(12,3) NOT NULL,
  power_kw NUMERIC(8,3),
  is_estimated BOOLEAN DEFAULT false,
  source TEXT -- np. "wago-pfc300", "manual", "api"
);

-- Szablony taryfowe (konfigurowane przez zarządcę)
CREATE TABLE tariff_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id),
  name TEXT NOT NULL, -- np. "G11 – ZAEL 2026"
  tariff_group TEXT DEFAULT 'G11',
  margin_pct NUMERIC(5,2) DEFAULT 0, -- marża zarządcy w %
  vat_rate NUMERIC(4,2) DEFAULT 23,
  valid_from DATE NOT NULL,
  valid_to DATE
);

-- Składniki taryfy (na podstawie faktury ZAEL)
CREATE TABLE tariff_components (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tariff_id UUID REFERENCES tariff_templates(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  component_type TEXT NOT NULL, -- per_kwh | monthly_fixed | monthly_allocated
  unit_price NUMERIC(10,5) NOT NULL,
  unit TEXT DEFAULT 'zł/kWh', -- zł/kWh | zł/mc
  vat_rate NUMERIC(4,2) DEFAULT 23,
  allocation_method TEXT DEFAULT 'proportional' -- proportional | equal (dla monthly)
);

-- Faktury wystawione najemcom
CREATE TABLE invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id),
  invoice_no TEXT UNIQUE NOT NULL, -- np. "FV/001/05/2026"
  period_from DATE NOT NULL,
  period_to DATE NOT NULL,
  kwh_consumed NUMERIC(10,3),
  net_amount NUMERIC(10,2),
  vat_amount NUMERIC(10,2),
  gross_amount NUMERIC(10,2),
  status TEXT DEFAULT 'draft', -- draft | ready | sent | paid | overdue
  due_date DATE,
  sent_at TIMESTAMPTZ,
  pdf_path TEXT, -- ścieżka w Supabase Storage
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Pozycje faktury (szczegółowy breakdown)
CREATE TABLE invoice_lines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
  component_id UUID REFERENCES tariff_components(id),
  label TEXT NOT NULL,
  quantity NUMERIC(10,3),
  unit TEXT,
  unit_price NUMERIC(10,5),
  net_amount NUMERIC(10,2),
  vat_rate NUMERIC(4,2)
);
```

### Przykładowe dane taryfowe (ZAEL-Energo G11, 2026)

```sql
-- Składniki dla taryfy G11 na podstawie faktury ZAEL FV/E/1728/04/2026
INSERT INTO tariff_components (tariff_id, name, component_type, unit_price, unit) VALUES
  (:tariff_id, 'Opłata obrotowa (energia)', 'per_kwh', 0.51760, 'zł/kWh'),
  (:tariff_id, 'Opłata zmienna sieciowa',   'per_kwh', 0.25660, 'zł/kWh'),
  (:tariff_id, 'Opłata jakościowa',          'per_kwh', 0.03320, 'zł/kWh'),
  (:tariff_id, 'Opłata OZE',                 'per_kwh', 0.00730, 'zł/kWh'),
  (:tariff_id, 'Opłata kogeneracyjna',        'per_kwh', 0.00300, 'zł/kWh'),
  (:tariff_id, 'Opłata mocowa',          'monthly_fixed',  17.18, 'zł/mc'),
  (:tariff_id, 'Abonament',             'monthly_fixed',   5.00, 'zł/mc'),
  (:tariff_id, 'Opłata stała sieciowa', 'monthly_fixed',   5.25, 'zł/mc');
-- Suma netto per kWh (zmienne): 0,8157 zł/kWh
-- Opłaty stałe miesięcznie: 27,43 zł/mc
```

---

## Logika biznesowa – silnik taryfowy

### Algorytm generowania faktury miesięcznej

```python
def generate_invoice(tenant_id, period_from, period_to):
    # 1. Pobierz aktywne przypisanie licznika
    assignment = get_active_assignment(tenant_id, period_from, period_to)
    meter = get_meter(assignment.meter_id)
    
    # 2. Pobierz odczyty z okresu
    reading_start = get_reading_at(meter.id, period_from)
    reading_end = get_reading_at(meter.id, period_to)
    kwh_consumed = reading_end.value_kwh - reading_start.value_kwh
    
    # 3. Pobierz aktywną taryfę
    tariff = get_active_tariff(meter.tariff_id, period_from)
    components = get_tariff_components(tariff.id)
    
    # 4. Oblicz pozycje faktury
    lines = []
    for component in components:
        if component.component_type == 'per_kwh':
            net = round(kwh_consumed * component.unit_price, 2)
            lines.append(InvoiceLine(
                label=component.name,
                quantity=kwh_consumed,
                unit='kWh',
                unit_price=component.unit_price,
                net_amount=net,
                vat_rate=component.vat_rate
            ))
        
        elif component.component_type == 'monthly_fixed':
            # Opłaty stałe: alokacja proporcjonalna lub równa
            if component.allocation_method == 'proportional':
                total_kwh = get_total_building_kwh(meter.building_id, period_from, period_to)
                share = kwh_consumed / total_kwh if total_kwh > 0 else 0
                net = round(component.unit_price * share, 2)
            else:  # equal – stała kwota per lokal
                net = component.unit_price
            
            lines.append(InvoiceLine(
                label=component.name,
                quantity=1,
                unit='mc',
                unit_price=net,
                net_amount=net,
                vat_rate=component.vat_rate
            ))
    
    # 5. Opcjonalna marża zarządcy
    if tariff.margin_pct > 0:
        subtotal = sum(l.net_amount for l in lines)
        margin = round(subtotal * tariff.margin_pct / 100, 2)
        lines.append(InvoiceLine(label='Opłata za obsługę', net_amount=margin, vat_rate=23))
    
    # 6. Sumuj i zapisz fakturę
    net_total = sum(l.net_amount for l in lines)
    vat_total = sum(round(l.net_amount * l.vat_rate / 100, 2) for l in lines)
    
    invoice = Invoice(
        tenant_id=tenant_id,
        invoice_no=generate_invoice_no(period_from),
        period_from=period_from,
        period_to=period_to,
        kwh_consumed=kwh_consumed,
        net_amount=net_total,
        vat_amount=vat_total,
        gross_amount=net_total + vat_total,
        due_date=period_to + timedelta(days=14),
        status='ready'
    )
    
    return invoice, lines
```

---

## Zakres MVP (fazy)

### Faza 1 – Backend core (zacznij tutaj)

**Cel:** działający API który przyjmuje odczyty i generuje faktury.

Deliverables:
- [ ] Migracje SQL (wszystkie tabele powyżej) dla Supabase
- [ ] FastAPI app z podstawową strukturą (`/api/v1/`)
- [ ] Auth: JWT przez Supabase Auth, middleware `get_current_org()`
- [ ] Endpoint `POST /readings` – przyjmuje odczyty z gateway
- [ ] Endpoint `GET /readings/{meter_id}` – historia odczytów
- [ ] Endpoint `POST /invoices/generate` – uruchamia silnik taryfowy
- [ ] Endpoint `GET /invoices/{tenant_id}` – lista faktur najemcy
- [ ] Generator PDF faktur (WeasyPrint) – szablon HTML → PDF
- [ ] Upload PDF do Supabase Storage

Stack:
```
fastapi==0.111.0
supabase==2.5.0
celery==5.4.0
redis==5.0.4
weasyprint==62.3
python-jose==3.3.0  # JWT
pydantic==2.7.0
```

Struktura projektu:
```
energybill/
├── api/
│   ├── main.py
│   ├── deps.py          # get_current_user, get_current_org
│   ├── routers/
│   │   ├── readings.py
│   │   ├── invoices.py
│   │   ├── meters.py
│   │   ├── tenants.py
│   │   └── tariffs.py
│   └── schemas/         # Pydantic models
├── core/
│   ├── billing_engine.py   # silnik taryfowy
│   ├── pdf_generator.py    # WeasyPrint
│   └── invoice_numbering.py
├── db/
│   ├── migrations/
│   │   └── 001_initial.sql
│   └── supabase_client.py
├── tasks/
│   └── celery_tasks.py     # miesięczny scheduler
├── templates/
│   └── invoice.html        # szablon PDF faktury
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

### Faza 2 – Agent gateway (lokalny M-Bus reader)

Osobny skrypt Python do uruchomienia na WAGO PFC300 lub RPi:

```python
# gateway_agent/agent.py
# Czyta liczniki M-Bus i wysyła odczyty do API

import requests
import schedule
import time
from mbus import MBus  # python-mbus lub własna implementacja

API_URL = "https://api.energybill.pl/api/v1/readings"
API_KEY = "org_key_xxx"  # klucz API organizacji

def read_and_push():
    mbus = MBus(device='/dev/ttyUSB0', baudrate=2400)
    
    meters = [
        {"mbus_address": "05", "meter_id": "uuid-meter-u1"},
        {"mbus_address": "06", "meter_id": "uuid-meter-u2"},
        # ...
    ]
    
    for m in meters:
        record = mbus.read(m["mbus_address"])
        payload = {
            "meter_id": m["meter_id"],
            "value_kwh": record.energy_kwh,
            "power_kw": record.power_kw,
            "read_type": "remote",
            "source": "wago-pfc300"
        }
        requests.post(API_URL, json=payload,
                      headers={"X-API-Key": API_KEY})

schedule.every(15).minutes.do(read_and_push)
while True:
    schedule.run_pending()
    time.sleep(1)
```

### Faza 3 – Frontend panel zarządcy

React + Vite + Tailwind + Supabase JS:

Widoki do zbudowania (w kolejności priorytetu):
1. **Dashboard** – podsumowanie: liczniki, ostatnie odczyty, faktury do wysłania
2. **Budynki i liczniki** – CRUD: dodaj budynek, dodaj licznik, przypisz najemcę
3. **Najemcy** – lista, dane, historia faktur, status płatności
4. **Taryfy** – konfiguracja szablonów taryfowych i składników
5. **Faktury** – generuj, podgląd PDF, wyślij email, oznacz jako opłacona

### Faza 4 – Portal najemcy

Oddzielna trasa `/portal/:token`:
- Bez logowania – dostęp przez unikalny token (UUID w tabeli `tenants.portal_token`)
- Widoki: przegląd bieżącego miesiąca, historia zużycia (wykres), lista faktur + pobierz PDF
- Token ważny 90 dni, potem regenerowany przy wysyłce kolejnej faktury

---

## Format faktury PDF (wzorzec z faktury ZAEL)

Faktura musi zawierać:
- Nagłówek: logo zarządcy, nr faktury (format `FV/XXX/MM/YYYY`), data wystawienia, miesiąc sprzedaży
- Dane sprzedawcy (zarządca) i nabywcy (najemca) – z NIP jeśli firma
- Tabela pozycji: nazwa składnika, ilość, jednostka, cena netto, VAT%, wartość brutto
- Podsumowanie: razem netto, VAT, razem brutto (słownie)
- Informacje o płatności: kwota, termin, nr konta bankowego
- Dane pomiarowe: wskazanie licznika poprzednie → bieżące, kWh, typ odczytu

Przykład na podstawie faktury ZAEL (kwiecień 2026, 177 kWh, kwota 211,77 zł brutto):
```
Opłata obrotowa       177 kWh × 0,5176 zł/kWh =  91,62 zł netto  23% VAT  112,69 zł brutto
Opłata zmienna siec.  177 kWh × 0,2566 zł/kWh =  45,42 zł netto  23% VAT   55,87 zł brutto
Opłata jakościowa     177 kWh × 0,0332 zł/kWh =   5,88 zł netto  23% VAT    7,23 zł brutto
Opłata OZE            177 kWh × 0,0073 zł/kWh =   1,29 zł netto  23% VAT    1,59 zł brutto
Opłata kogeneracyjna  177 kWh × 0,0030 zł/kWh =   0,53 zł netto  23% VAT    0,65 zł brutto
Opłata mocowa              1 mc × 17,18 zł/mc  =  17,18 zł netto  23% VAT   21,13 zł brutto
Abonament                  1 mc ×  5,00 zł/mc  =   5,00 zł netto  23% VAT    6,15 zł brutto
Opłata stała sieciowa      1 mc ×  5,25 zł/mc  =   5,25 zł netto  23% VAT    6,46 zł brutto
─────────────────────────────────────────────────────────────────────────────────────────────
RAZEM                                              172,17 zł netto          211,77 zł brutto
```

---

## API – kluczowe endpointy

```
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh

GET    /api/v1/organizations/me
PATCH  /api/v1/organizations/me

GET    /api/v1/buildings
POST   /api/v1/buildings
GET    /api/v1/buildings/{id}
PATCH  /api/v1/buildings/{id}

GET    /api/v1/meters?building_id=...
POST   /api/v1/meters
GET    /api/v1/meters/{id}/readings

POST   /api/v1/readings              # używany przez gateway agent
GET    /api/v1/readings/{meter_id}

GET    /api/v1/tenants?building_id=...
POST   /api/v1/tenants
GET    /api/v1/tenants/{id}
PATCH  /api/v1/tenants/{id}

GET    /api/v1/tariffs
POST   /api/v1/tariffs
POST   /api/v1/tariffs/{id}/components

POST   /api/v1/invoices/generate     # body: {building_id, period_from, period_to}
GET    /api/v1/invoices?tenant_id=...&status=...
GET    /api/v1/invoices/{id}
POST   /api/v1/invoices/{id}/send    # wysyła email z PDF
PATCH  /api/v1/invoices/{id}/status  # oznacz jako opłacona

# Portal najemcy (publiczny, auth przez token)
GET    /api/v1/portal/{token}/overview
GET    /api/v1/portal/{token}/readings
GET    /api/v1/portal/{token}/invoices
GET    /api/v1/portal/{token}/invoices/{id}/pdf
```

---

## Docker Compose (docelowy deployment)

```yaml
version: '3.9'
services:
  api:
    build: .
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - redis
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000

  worker:
    build: .
    env_file: .env
    depends_on:
      - redis
    command: celery -A tasks.celery_tasks worker --beat --loglevel=info

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  frontend:
    build: ./frontend
    ports:
      - "3000:80"

volumes:
  redis_data:
```

---

## .env.example

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...

# Redis (Celery)
REDIS_URL=redis://redis:6379/0

# Email (Resend)
RESEND_API_KEY=re_...
FROM_EMAIL=faktury@twojadomena.pl

# App
SECRET_KEY=twoj-tajny-klucz-min-32-znaki
ENVIRONMENT=development
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Celery – harmonogram generowania faktur
INVOICE_GENERATION_DAY=1       # 1. dzień miesiąca
INVOICE_DUE_DAYS=14            # termin płatności w dniach
```

---

## Kolejność implementacji (zatwierdzona)

```
Tydzień 1:
  [x] Projekt architektury (gotowe)
  [x] Schemat bazy danych (gotowe)
  [ ] Migracje SQL → Supabase
  [ ] FastAPI boilerplate + auth middleware

Tydzień 2:
  [ ] Endpointy readings + meters + tenants
  [ ] Silnik taryfowy (billing_engine.py)
  [ ] Generator PDF (WeasyPrint + szablon HTML)

Tydzień 3:
  [ ] Endpoint generowania faktur
  [ ] Wysyłka email (Resend)
  [ ] Celery scheduler (1. dnia miesiąca)

Tydzień 4:
  [ ] Frontend – panel zarządcy (React)
  [ ] Portal najemcy (token-based)
  [ ] Docker Compose + deploy na VPS

Demo:
  [ ] Seed data: 1 budynek, 3 najemców, 6 miesięcy odczytów
  [ ] Wygeneruj faktury, wyślij emailem, pokaż portal najemcy
```

---

## Uwagi implementacyjne

**Multi-tenancy:** Każde zapytanie do bazy musi filtrować po `org_id`. Użyj middleware
który wyciąga `org_id` z JWT i wstrzykuje do wszystkich queries. Rozważ Supabase RLS
(Row Level Security) jako dodatkową warstwę ochrony.

**Numery faktur:** Format `FV/NUMER/MM/YYYY` gdzie NUMER jest sekwencyjny per organizacja
per miesiąc. Użyj transakcji bazodanowej żeby uniknąć duplikatów.

**Obsługa niepełnych miesięcy:** Gdy najemca wprowadził się 15. dnia miesiąca, system
musi rozliczyć tylko od `meter_assignments.valid_from` do końca miesiąca. Opłaty stałe
rozliczaj proporcjonalnie do liczby dni.

**Brak odczytu:** Jeśli brak odczytu na koniec okresu, użyj ostatniego dostępnego odczytu
i oznacz fakturę jako `is_estimated=true`. Zarządca musi potwierdzić przed wysyłką.

**Gateway auth:** Agent lokalny autoryzuje się przez `X-API-Key` w headerze (nie JWT).
Klucze API przechowuj w osobnej tabeli `api_keys` z `org_id` i `last_used_at`.

**WeasyPrint na Docker:** Wymaga libcairo, pango i fontconfig. Użyj base image:
`FROM python:3.12-slim` i doinstaluj: `apt-get install -y libcairo2 libpango-1.0-0
libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`

**Statusy płatności faktur – decyzja MVP:**
Na MVP stosujemy ręczne oznaczanie płatności przez zarządcę. Nie ma integracji bankowej.

Trzy etapy (zaplanowane na przyszłość, NIE implementować w MVP):
- Faza 1 MVP: ręczne `PATCH /invoices/{id}/status` z UI – jedno kliknięcie "Oznacz jako opłacona"
- Faza 2 (po MVP): import wyciągu bankowego CSV/MT940 – system dopasowuje przelewy do faktur
- Faza 3 (przyszłość): wirtualne numery kont + API bankowe – pełna automatyzacja

W emailu z fakturą zawsze umieszczaj gotowy blok płatności:
```
Tytuł przelewu: {invoice_no} – {tenant_name}
Nr konta:       {org_bank_account}
Kwota:          {gross_amount} zł
Termin:         {due_date}
```
Dzięki temu zarządca widzi numer faktury w tytule przelewu na wyciągu bankowym
i może szybko ręcznie oznaczyć fakturę jako opłaconą.

## Mockupy UI (zatwierdzone – Claude Design)

Wszystkie ekrany zostały zaprojektowane w Claude Design. Styl: ciemny sidebar
(#1a2e1a), akcent zielony (#2d6a2d), białe tło główne, semantyczne kolory
(zielony = OK, czerwony = problem, pomarańczowy = uwaga).

Zatwierdzone ekrany:
- **Dashboard** – wariant "Kafelki per budynek" jako domyślny + "Co wymaga uwagi dziś"
  jako drugi wariant. Każdy kafelek budynku: liczniki online/offline, faktury do wysłania,
  zaległe płatności, suma kWh/mc.
- **Budynki** – tabela z kolumnami: nazwa, taryfa, liczniki (X/Y), najemcy, do wysłania,
  zaległe. Przycisk "+ Dodaj budynek" w prawym górnym rogu.
- **Liczniki** – tabela z filtrem po budynku, kolumny: lokal, budynek, nr seryjny M-Bus,
  ostatni odczyt (kWh), kiedy, status (online/offline/szacowany), trend 10 mc (sparkline).
  Przycisk "+ Dodaj licznik".
- **Najemcy** – tabela z filtrem po budynku, kolumny: najemca, budynek/lokal, typ
  (os. fizyczna / firma·VAT), email, ostatnia faktura, płatność. Przycisk "+ Dodaj najemcę".
- **Taryfy** – szablon G11 z tabelą składników: nazwa, typ (per_kwh/monthly_fixed),
  cena netto, VAT%, cena brutto. Sumy: zmienna 0,8177 zł/kWh, stała 27,43 zł/mc.
  Przycisk "+ Dodaj taryfę".
- **Faktury** – filtry statusu (Wszystkie/Szkice/Gotowe/Wysłane/Opłacone/Po terminie),
  checkbox akcji masowych, przyciski "Generuj zaznaczone" / "Wyślij zaznaczone".
  Kolumny: nr faktury, najemca, lokal, okres, kWh, brutto, status, termin.

Brakujące ekrany do zaprojektowania (formularze CRUD – dodać przed implementacją frontendu):
- Modal "Dodaj/edytuj budynek"
- Modal "Dodaj/edytuj licznik" z przypisaniem do najemcy
- Modal "Dodaj/edytuj najemcę" z przypisaniem licznika
- Panel "Dodaj taryfę" z możliwością klonowania istniejącej

---

## Odpowiedzialność prawna – granica systemu

System jest narzędziem, nie doradcą podatkowym ani energetycznym.

W regulaminie/umowie z klientem zawrzeć:
> "System generuje dokumenty na podstawie danych wprowadzonych przez użytkownika.
> Dostawca nie ponosi odpowiedzialności za zgodność rozliczeń z przepisami prawa
> energetycznego i podatkowego."

Co leży po stronie systemu (nasza odpowiedzialność):
- Poprawny odczyt licznika i zapis do bazy
- Poprawne wyliczenie według wprowadzonej taryfy
- Wygenerowanie poprawnie sformatowanego dokumentu PDF
- Wysyłka emailem i archiwizacja przez 5 lat w Supabase Storage

Co leży po stronie zarządcy (jego odpowiedzialność):
- Legalizacja liczników
- Zgodność taryfy z umową z dystrybutorem
- Zgodność faktury z przepisami podatkowymi
- Rejestracja jako podatnik VAT (jeśli wystawia faktury VAT)
- Marża – jej legalność wobec najemców



Pierwsza sesja w Claude Code:

> "Zacznijmy od Fazy 1. Najpierw stwórz plik migracji SQL `db/migrations/001_initial.sql`
> ze wszystkimi tabelami z pliku ENERGYBILL_MVP_PROMPT.md, a następnie boilerplate
> FastAPI w `api/main.py` z podstawową strukturą routerów i middleware auth przez
> Supabase JWT. Przed implementacją przedstaw plan."
