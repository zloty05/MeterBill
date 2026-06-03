-- ============================================================================
-- EnergyBill — migracja 003: GRANT-y dla roli service_role
--
-- Projekt Supabase założono z opcją "Automatically expose new tables" = OFF.
-- Skutek: role Data API (service_role, anon, authenticated) NIE dostają
-- automatycznie uprawnień do tabel w schemacie public. Backend działa na
-- SERVICE_KEY (rola service_role) i bez tych GRANT-ów dostaje:
--   permission denied for table organizations (SQLSTATE 42501)
--
-- Tu nadajemy service_role pełny dostęp do public (backend systemowy: gateway
-- readings, generowanie faktur, scheduler). Izolację org_id wymusza warstwa
-- aplikacji (api/deps.py); RLS jest dodatkową siatką dla anon/authenticated.
--
-- Role anon/authenticated (klucz publiczny, supabase-js w przeglądarce) celowo
-- NIE dostają tu uprawnień — dodamy je świadomie i wąsko przy budowie frontendu
-- (faza 3), tylko na tabelach, które front ma widzieć.
-- ============================================================================

-- Dostęp do schematu
GRANT USAGE ON SCHEMA public TO service_role;

-- Pełen dostęp do istniejących tabel i sekwencji
GRANT ALL ON ALL TABLES    IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Wywoływanie funkcji (m.in. next_invoice_no)
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Domyślne uprawnienia dla obiektów tworzonych w przyszłości w public.
-- Dzięki temu kolejne migracje nie muszą powtarzać GRANT-ów dla service_role.
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO service_role;
