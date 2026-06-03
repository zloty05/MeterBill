-- ============================================================================
-- EnergyBill — migracja 002: atomowa numeracja faktur
--
-- Numer faktury FV/NNN/MM/YYYY jest sekwencyjny per organizacja per miesiąc
-- (ENERGYBILL_MVP_PROMPT.md l. 606-607). Tabela invoice_sequences istnieje już
-- w migracji 001. Tu dodajemy funkcję, która atomowo rezerwuje kolejny numer.
--
-- Dlaczego funkcja, a nie UPDATE z aplikacji:
-- Supabase REST (PostgREST) nie pozwala na atomowe "UPDATE ... RETURNING" przy
-- współbieżności w jednym wywołaniu HTTP. INSERT ... ON CONFLICT DO UPDATE w
-- funkcji plpgsql blokuje wiersz (FOR UPDATE w ramach upsertu) i gwarantuje brak
-- duplikatów numerów nawet przy równoległym generowaniu w tej samej org/miesiącu.
--
-- Wywołanie z backendu: client.rpc("next_invoice_no", {p_org_id, p_year, p_month})
-- Zwraca: kolejny numer porządkowy (INT). Format FV/... składa aplikacja.
-- ============================================================================

CREATE OR REPLACE FUNCTION next_invoice_no(
  p_org_id UUID,
  p_year   INT,
  p_month  INT
)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
  v_no INT;
BEGIN
  INSERT INTO invoice_sequences (org_id, year, month, last_no)
  VALUES (p_org_id, p_year, p_month, 1)
  ON CONFLICT (org_id, year, month)
  DO UPDATE SET last_no = invoice_sequences.last_no + 1
  RETURNING last_no INTO v_no;

  RETURN v_no;
END;
$$;
