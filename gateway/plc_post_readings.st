(*
  SZKIC referencyjny — Codesys ST dla WAGO 750-8217 (PFC200 + 4G).
  NIE jest to gotowy, skompilowany program. To szkielet pokazujący kontrakt
  POST /readings od strony sterownika: zbudowanie JSON, nagłówek X-API-Key,
  obsługa wyniku i zarys retry/bufora przy zerwanym łączu 4G.

  Dostosuj do swojego firmware / bibliotek:
    - HTTPS: WagoAppCloud / CmpHttpClient / NetBaseServices (zależnie od wersji).
    - JSON:  WagoAppJSON lub ręczne sklejanie stringów (jak niżej).
    - CA cert: wgrany na sterownik (Security Screen / certyfikaty), inaczej TLS padnie.

  Kontrakt (patrz README.md):
    POST {API_URL}
    Header: X-API-Key: <klucz z scripts/make_api_key.py>
    Body  : {"meter_id":"<uuid>","value_kwh":<liczba>,"read_type":"remote","source":"wago-pfc200"}
    Odpowiedź: 201 zapisano | 200 duplikat (idempotencja) | 401 zły klucz | 404 zły meter | 422 zła wartość
    read_at pomijamy — czas nadaje serwer.
*)

FUNCTION_BLOCK FB_PushReading
VAR_INPUT
    xTrigger    : BOOL;            // narastające zbocze = wyślij
    sMeterId    : STRING(64);      // uuid licznika z bazy
    rValueKwh   : LREAL;           // odczyt z licznika (kWh)
END_VAR
VAR_OUTPUT
    xDone       : BOOL;
    xError      : BOOL;
    iHttpStatus : INT;             // 201/200 = ok
END_VAR
VAR
    sUrl        : STRING(255) := 'https://api.energybill.pl/api/v1/readings';
    sApiKey     : STRING(128) := '<<KLUCZ_API>>';   // wgraj bezpiecznie, nie do repo publicznego
    sBody       : STRING(512);
    sValue      : STRING(32);
    iRetry      : INT;
    iMaxRetry   : INT := 3;
    // fbHttp   : <typ klienta HTTP z Twojej biblioteki>;   // np. WagoAppCloud / CmpHttpClient
END_VAR

// --- 1. Złożenie JSON (ręczne; LREAL_TO_STRING bo brak natywnego JSON w starszym fw) ---
sValue := LREAL_TO_STRING(rValueKwh);
sBody  := CONCAT('{"meter_id":"', sMeterId);
sBody  := CONCAT(sBody, '","value_kwh":');
sBody  := CONCAT(sBody, sValue);
sBody  := CONCAT(sBody, ',"read_type":"remote","source":"wago-pfc200"}');

// --- 2. Wysyłka HTTPS z nagłówkiem X-API-Key ---
// Pseudokod — podstaw wywołania swojego FB klienta HTTP:
//   fbHttp(xExecute := xTrigger,
//          sUrl := sUrl,
//          sMethod := 'POST',
//          sHeader := CONCAT('X-API-Key: ', sApiKey),       // + Content-Type: application/json
//          sRequestBody := sBody);
//   iHttpStatus := fbHttp.iStatusCode;
//   xDone := fbHttp.xDone;
//   xError := fbHttp.xError;

// --- 3. Retry/bufor przy zerwanym 4G (zarys maszyny stanów) ---
// Jeśli xError (timeout/brak sieci): zapisz sBody do bufora (np. tablica w pamięci
// nieulotnej / plik na karcie), zwiększ iRetry i ponów w kolejnym cyklu z backoff.
// Po sukcesie (iHttpStatus IN (200,201)) usuń odczyt z bufora.
// 4xx (401/404/422) NIE ponawiaj — to błąd konfiguracji (zły klucz/meter/wartość),
//   zgłoś alarm operatorowi zamiast zapętlać.
IF iHttpStatus = 200 OR iHttpStatus = 201 THEN
    iRetry := 0;
    xDone  := TRUE;
    xError := FALSE;
ELSIF iHttpStatus >= 400 AND iHttpStatus < 500 THEN
    xError := TRUE;   // błąd trwały — alarm, nie ponawiaj
ELSE
    // 0 (brak odpowiedzi) lub 5xx → ponów, dopóki iRetry < iMaxRetry
    IF iRetry < iMaxRetry THEN
        iRetry := iRetry + 1;
        // (tu: dodaj do bufora offline + ponów w kolejnym cyklu z opóźnieniem)
    END_IF
END_IF
