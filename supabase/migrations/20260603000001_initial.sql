-- ============================================================================
-- EnergyBill MVP — migracja inicjalna
-- Faza 1: schemat bazy danych (PostgreSQL / Supabase)
--
-- Zawiera tabele ze specyfikacji (ENERGYBILL_MVP_PROMPT.md l. 84-212) oraz
-- uzupełnienia ustalone w analizie:
--   - api_keys            (gateway auth przez X-API-Key)
--   - invoice_sequences   (bezpieczna numeracja FV/NUMER/MM/YYYY)
--   - organizations: bank_account, address, dane sprzedawcy
--   - tenants.token_expires_at (rotacja portal_token co 90 dni)
--   - invoices.issued_date
--   - public.users.id = auth.users.id (mapowanie 1:1)
--   - readings UNIQUE(meter_id, read_at) (idempotencja POST /readings)
--   - RLS na org_id (hybryda: RLS + filtr w warstwie aplikacji)
--   - indeksy FK
-- ============================================================================

-- ----------------------------------------------------------------------------
-- ENUMy (zamiast luźnych TEXT — czytelniejsze i bezpieczniejsze)
-- ----------------------------------------------------------------------------
CREATE TYPE org_plan        AS ENUM ('free', 'pro', 'enterprise');
CREATE TYPE user_role       AS ENUM ('admin', 'viewer');
CREATE TYPE meter_protocol  AS ENUM ('mbus', 'modbus', 'opcua', 'manual');
CREATE TYPE reading_type    AS ENUM ('remote', 'physical', 'estimated');
CREATE TYPE component_type  AS ENUM ('per_kwh', 'monthly_fixed', 'monthly_allocated');
CREATE TYPE allocation_method AS ENUM ('proportional', 'equal');
CREATE TYPE invoice_status  AS ENUM ('draft', 'ready', 'sent', 'paid', 'overdue');

-- ----------------------------------------------------------------------------
-- organizations — multi-tenancy: każdy zarządca = osobna organizacja
-- (rozszerzone o dane sprzedawcy potrzebne na fakturze PDF)
-- ----------------------------------------------------------------------------
CREATE TABLE organizations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  nip           TEXT,
  address       TEXT,                       -- adres sprzedawcy na fakturze
  bank_account  TEXT,                       -- nr konta do bloku płatności
  plan          org_plan DEFAULT 'free',
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- users — profile zarządców; id = auth.users.id (mapowanie 1:1 na Supabase Auth)
-- ----------------------------------------------------------------------------
CREATE TABLE users (
  id        UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  org_id    UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email     TEXT UNIQUE NOT NULL,
  role      user_role DEFAULT 'admin',
  active    BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- api_keys — autoryzacja lokalnego gateway agenta (X-API-Key)
-- Przechowujemy hash klucza, nie plaintext.
-- ----------------------------------------------------------------------------
CREATE TABLE api_keys (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name          TEXT,                       -- np. "Gateway Rynek 12"
  key_hash      TEXT NOT NULL,              -- sha256 klucza
  key_prefix    TEXT,                       -- pierwsze znaki do identyfikacji w UI
  active        BOOLEAN DEFAULT true,
  last_used_at  TIMESTAMPTZ,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- tariff_templates — szablony taryfowe (konfigurowane przez zarządcę)
-- (definiowane przed meters, bo meters.tariff_id na nie wskazuje)
-- ----------------------------------------------------------------------------
CREATE TABLE tariff_templates (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,              -- np. "G11 – ZAEL 2026"
  tariff_group  TEXT DEFAULT 'G11',
  margin_pct    NUMERIC(5,2) DEFAULT 0,     -- marża zarządcy w %
  vat_rate      NUMERIC(4,2) DEFAULT 23,
  source_doc    TEXT,                       -- nr faktury źródłowej, np. "FV/E/1728/04/2026"
  valid_from    DATE NOT NULL,
  valid_to      DATE
);

-- ----------------------------------------------------------------------------
-- tariff_components — składniki taryfy (na podstawie faktury dystrybutora)
-- ----------------------------------------------------------------------------
CREATE TABLE tariff_components (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tariff_id         UUID NOT NULL REFERENCES tariff_templates(id) ON DELETE CASCADE,
  name              TEXT NOT NULL,
  component_type    component_type NOT NULL,        -- per_kwh | monthly_fixed | monthly_allocated
  unit_price        NUMERIC(10,5) NOT NULL,
  unit              TEXT DEFAULT 'zł/kWh',          -- zł/kWh | zł/mc
  vat_rate          NUMERIC(4,2) DEFAULT 23,
  allocation_method allocation_method DEFAULT 'proportional', -- rezerwa; MVP używa monthly_fixed
  sort_order        INT DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- buildings — budynki zarządcy
-- ----------------------------------------------------------------------------
CREATE TABLE buildings (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  address         TEXT NOT NULL,
  main_meter_ppe  TEXT,                     -- kod PPE licznika głównego od dystrybutora
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- meters — podliczniki w budynku
-- ----------------------------------------------------------------------------
CREATE TABLE meters (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  building_id   UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
  tariff_id     UUID REFERENCES tariff_templates(id),
  serial_no     TEXT NOT NULL,
  mbus_address  TEXT,                       -- adres M-Bus (hex, np. "05")
  protocol      meter_protocol DEFAULT 'mbus',
  ppe_code      TEXT,
  tariff_group  TEXT DEFAULT 'G11',         -- G11 | G12
  label         TEXT,                       -- np. "Lokal U1 – parter"
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- tenants — najemcy
-- ----------------------------------------------------------------------------
CREATE TABLE tenants (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  building_id       UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
  name              TEXT NOT NULL,
  email             TEXT NOT NULL,
  nip               TEXT,                   -- jeśli firma; puste = rachunek (MVP: bez rozróżnienia dokumentu)
  unit_no           TEXT NOT NULL,          -- nr lokalu np. "U1", "M3"
  active            BOOLEAN DEFAULT true,
  portal_token      TEXT UNIQUE,            -- jednorazowy token do portalu (UUID)
  token_expires_at  TIMESTAMPTZ,            -- ważność tokenu (rotacja co 90 dni)
  created_at        TIMESTAMPTZ DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- meter_assignments — przypisanie licznika do najemcy (z historią)
-- ----------------------------------------------------------------------------
CREATE TABLE meter_assignments (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  meter_id    UUID NOT NULL REFERENCES meters(id) ON DELETE CASCADE,
  valid_from  DATE NOT NULL,
  valid_to    DATE                          -- NULL = aktywne
);

-- ----------------------------------------------------------------------------
-- readings — odczyty liczników
-- UNIQUE(meter_id, read_at) zapewnia idempotencję POST /readings (retry gateway)
-- ----------------------------------------------------------------------------
CREATE TABLE readings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meter_id      UUID NOT NULL REFERENCES meters(id) ON DELETE CASCADE,
  read_at       TIMESTAMPTZ NOT NULL,
  read_type     reading_type DEFAULT 'remote',
  value_kwh     NUMERIC(12,3) NOT NULL,
  power_kw      NUMERIC(8,3),
  is_estimated  BOOLEAN DEFAULT false,
  source        TEXT,                       -- np. "wago-pfc300", "manual", "api"
  created_at    TIMESTAMPTZ DEFAULT now(),
  UNIQUE (meter_id, read_at)
);

-- ----------------------------------------------------------------------------
-- invoices — faktury wystawione najemcom
-- ----------------------------------------------------------------------------
CREATE TABLE invoices (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  tenant_id     UUID NOT NULL REFERENCES tenants(id),
  invoice_no    TEXT UNIQUE NOT NULL,       -- np. "FV/001/05/2026"
  period_from   DATE NOT NULL,
  period_to     DATE NOT NULL,
  issued_date   DATE,                       -- data wystawienia (≠ created_at)
  kwh_consumed  NUMERIC(10,3),
  net_amount    NUMERIC(10,2),
  vat_amount    NUMERIC(10,2),
  gross_amount  NUMERIC(10,2),
  status        invoice_status DEFAULT 'draft',
  due_date      DATE,
  sent_at       TIMESTAMPTZ,
  paid_at       TIMESTAMPTZ,
  is_estimated  BOOLEAN DEFAULT false,      -- faktura na odczycie szacowanym (wymaga potwierdzenia)
  pdf_path      TEXT,                       -- ścieżka w Supabase Storage
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- invoice_lines — pozycje faktury (szczegółowy breakdown, snapshot ceny)
-- ----------------------------------------------------------------------------
CREATE TABLE invoice_lines (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  invoice_id    UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
  component_id  UUID REFERENCES tariff_components(id),
  label         TEXT NOT NULL,
  quantity      NUMERIC(10,3),
  unit          TEXT,
  unit_price    NUMERIC(10,5),
  net_amount    NUMERIC(10,2),
  vat_rate      NUMERIC(4,2),
  sort_order    INT DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- invoice_sequences — bezpieczna sekwencja numerów faktur
-- Numeracja FV/NUMER/MM/YYYY: NUMER sekwencyjny per org per miesiąc.
-- Użycie: UPDATE ... SET last_no = last_no + 1 RETURNING last_no (w transakcji).
-- ----------------------------------------------------------------------------
CREATE TABLE invoice_sequences (
  org_id    UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  year      INT NOT NULL,
  month     INT NOT NULL,
  last_no   INT NOT NULL DEFAULT 0,
  PRIMARY KEY (org_id, year, month)
);

-- ============================================================================
-- Indeksy na kluczach obcych (Postgres nie tworzy ich automatycznie)
-- ============================================================================
CREATE INDEX idx_users_org              ON users(org_id);
CREATE INDEX idx_api_keys_org           ON api_keys(org_id);
CREATE INDEX idx_api_keys_hash          ON api_keys(key_hash);
CREATE INDEX idx_buildings_org          ON buildings(org_id);
CREATE INDEX idx_meters_building        ON meters(building_id);
CREATE INDEX idx_meters_tariff          ON meters(tariff_id);
CREATE INDEX idx_tenants_building       ON tenants(building_id);
CREATE INDEX idx_tenants_token          ON tenants(portal_token);
CREATE INDEX idx_tariff_templates_org   ON tariff_templates(org_id);
CREATE INDEX idx_tariff_components_tariff ON tariff_components(tariff_id);
CREATE INDEX idx_assignments_tenant     ON meter_assignments(tenant_id);
CREATE INDEX idx_assignments_meter      ON meter_assignments(meter_id);
CREATE INDEX idx_readings_meter_time    ON readings(meter_id, read_at DESC);
CREATE INDEX idx_invoices_org           ON invoices(org_id);
CREATE INDEX idx_invoices_tenant        ON invoices(tenant_id);
CREATE INDEX idx_invoices_status        ON invoices(status);
CREATE INDEX idx_invoice_lines_invoice  ON invoice_lines(invoice_id);

-- ============================================================================
-- Row Level Security (RLS)
-- Hybryda: RLS jako siatka bezpieczeństwa. Backend działający na SERVICE_KEY
-- omija RLS (bypassrls) — izolację org_id wymusza także middleware aplikacji.
-- Polityki poniżej chronią dostęp w kontekście JWT zalogowanego usera (anon key).
--
-- Wzorzec: user widzi wiersze swojej organizacji. org_id usera bierzemy z
-- public.users (id = auth.uid()).
-- ============================================================================

-- Funkcja pomocnicza: org_id aktualnie zalogowanego usera
CREATE OR REPLACE FUNCTION current_org_id()
RETURNS UUID
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT org_id FROM public.users WHERE id = auth.uid()
$$;

ALTER TABLE organizations      ENABLE ROW LEVEL SECURITY;
ALTER TABLE users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys           ENABLE ROW LEVEL SECURITY;
ALTER TABLE buildings          ENABLE ROW LEVEL SECURITY;
ALTER TABLE meters             ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants            ENABLE ROW LEVEL SECURITY;
ALTER TABLE tariff_templates   ENABLE ROW LEVEL SECURITY;
ALTER TABLE tariff_components  ENABLE ROW LEVEL SECURITY;
ALTER TABLE meter_assignments  ENABLE ROW LEVEL SECURITY;
ALTER TABLE readings           ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices           ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_lines      ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_sequences  ENABLE ROW LEVEL SECURITY;

-- organizations: user widzi tylko swoją organizację
CREATE POLICY org_isolation ON organizations
  FOR ALL USING (id = current_org_id());

-- users: widzi userów swojej organizacji
CREATE POLICY users_isolation ON users
  FOR ALL USING (org_id = current_org_id());

-- Tabele z bezpośrednim org_id
CREATE POLICY api_keys_isolation ON api_keys
  FOR ALL USING (org_id = current_org_id());
CREATE POLICY buildings_isolation ON buildings
  FOR ALL USING (org_id = current_org_id());
CREATE POLICY tariff_templates_isolation ON tariff_templates
  FOR ALL USING (org_id = current_org_id());
CREATE POLICY invoices_isolation ON invoices
  FOR ALL USING (org_id = current_org_id());
CREATE POLICY invoice_sequences_isolation ON invoice_sequences
  FOR ALL USING (org_id = current_org_id());

-- Tabele z org_id pośrednio przez building
CREATE POLICY meters_isolation ON meters
  FOR ALL USING (
    building_id IN (SELECT id FROM buildings WHERE org_id = current_org_id())
  );
CREATE POLICY tenants_isolation ON tenants
  FOR ALL USING (
    building_id IN (SELECT id FROM buildings WHERE org_id = current_org_id())
  );

-- tariff_components przez tariff_templates
CREATE POLICY tariff_components_isolation ON tariff_components
  FOR ALL USING (
    tariff_id IN (SELECT id FROM tariff_templates WHERE org_id = current_org_id())
  );

-- readings przez meter → building
CREATE POLICY readings_isolation ON readings
  FOR ALL USING (
    meter_id IN (
      SELECT m.id FROM meters m
      JOIN buildings b ON b.id = m.building_id
      WHERE b.org_id = current_org_id()
    )
  );

-- meter_assignments przez tenant → building
CREATE POLICY assignments_isolation ON meter_assignments
  FOR ALL USING (
    tenant_id IN (
      SELECT t.id FROM tenants t
      JOIN buildings b ON b.id = t.building_id
      WHERE b.org_id = current_org_id()
    )
  );

-- invoice_lines przez invoice
CREATE POLICY invoice_lines_isolation ON invoice_lines
  FOR ALL USING (
    invoice_id IN (SELECT id FROM invoices WHERE org_id = current_org_id())
  );
