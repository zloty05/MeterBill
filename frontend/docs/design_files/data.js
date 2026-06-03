// Sample data for the EnergyBill app (mid-fi, real-ish numbers from the MVP prompt)
window.WF = (function () {
  const org = { name: "Zarządca Tarnów sp. z o.o.", user: "M. Wójcik", initials: "MW" };

  const nav = [
    { id: "dashboard", label: "Dashboard", icon: "grid" },
    { id: "budynki",   label: "Budynki",   icon: "building" },
    { id: "liczniki",  label: "Liczniki",  icon: "gauge" },
    { id: "najemcy",   label: "Najemcy",   icon: "users" },
    { id: "taryfy",    label: "Taryfy",    icon: "tag" },
    { id: "faktury",   label: "Faktury",   icon: "doc" },
  ];

  // ---- Tariff G11 (ZAEL 2026) ----
  const tariff = {
    name: "G11 – ZAEL 2026",
    group: "G11",
    vat: 23,
    margin: 0,
    validFrom: "2026-01-01",
    source: "FV/E/1728/04/2026",
    components: [
      { name: "Opłata obrotowa (energia)", type: "per_kwh",       price: 0.51760, unit: "zł/kWh", vat: 23 },
      { name: "Opłata zmienna sieciowa",   type: "per_kwh",       price: 0.25660, unit: "zł/kWh", vat: 23 },
      { name: "Opłata jakościowa",         type: "per_kwh",       price: 0.03320, unit: "zł/kWh", vat: 23 },
      { name: "Opłata OZE",                type: "per_kwh",       price: 0.00730, unit: "zł/kWh", vat: 23 },
      { name: "Opłata kogeneracyjna",      type: "per_kwh",       price: 0.00300, unit: "zł/kWh", vat: 23 },
      { name: "Opłata mocowa",             type: "monthly_fixed", price: 17.18,   unit: "zł/mc",  vat: 23 },
      { name: "Abonament",                 type: "monthly_fixed", price: 5.00,    unit: "zł/mc",  vat: 23 },
      { name: "Opłata stała sieciowa",     type: "monthly_fixed", price: 5.25,    unit: "zł/mc",  vat: 23 },
    ],
  };

  // ---- Buildings ----
  const buildings = [
    { id: "b1", name: "Kamienica Rynek 12",       addr: "ul. Rynek 12, Tarnów",   meters: 9,  online: 9,  tenants: 9,  toSend: 5, overdue: 1, kwh: "9 420",  ppe: "PL0037..1204" },
    { id: "b2", name: "Kamienica Długa 8",         addr: "ul. Długa 8, Tarnów",     meters: 8,  online: 7,  tenants: 8,  toSend: 4, overdue: 0, kwh: "6 880",  ppe: "PL0037..0881" },
    { id: "b3", name: "Biurowiec Plac Wolności 3", addr: "Plac Wolności 3, Tarnów", meters: 10, online: 10, tenants: 10, toSend: 4, overdue: 1, kwh: "21 050", ppe: "PL0037..3055" },
    { id: "b4", name: "Lokale Krakowska 45",       addr: "ul. Krakowska 45, Tarnów",meters: 5,  online: 5,  tenants: 5,  toSend: 2, overdue: 0, kwh: "4 110",  ppe: "PL0037..4509" },
  ];

  const shortName = { b1: "Rynek 12", b2: "Długa 8", b3: "Plac Wolności 3", b4: "Krakowska 45" };

  // ---- Meters + tenants generated per building ----
  function spark(seed, n = 10) {
    const out = []; let v = 40 + (seed % 30);
    for (let i = 0; i < n; i++) { v += ((seed * (i + 3)) % 17) - 8; v = Math.max(12, v); out.push(Math.round(v)); }
    return out;
  }
  const fmt = (n) => n.toLocaleString("pl-PL", { minimumFractionDigits: 3, maximumFractionDigits: 3 });

  const unitDefs = {
    b1: [
      ["U1 · parter", "Anna Kowalska", "os", "anna.kowalska@gmail.com", ""],
      ["U2 · parter", "Firma XYZ sp. z o.o.", "firma", "biuro@xyz.pl", "873-000-12-34"],
      ["M1 · I p.", "Tomasz Lewandowski", "os", "t.lewandowski@wp.pl", ""],
      ["M2 · I p.", "Katarzyna Nowak", "os", "k.nowak@gmail.com", ""],
      ["M3 · II p.", "Paweł Wiśniewski", "os", "pawel.w@onet.pl", ""],
      ["M4 · II p.", "Magdalena Dąbrowska", "os", "m.dabrowska@gmail.com", ""],
      ["M5 · III p.", "Robert Kamiński", "os", "r.kaminski@interia.pl", ""],
      ["M6 · III p.", "Joanna Zając", "os", "joanna.zajac@gmail.com", ""],
      ["M7 · poddasze", "Marek Szymański", "os", "m.szymanski@wp.pl", ""],
    ],
    b2: [
      ["U1 · parter", "Salon Fryzjerski Bella", "firma", "bella@salon.pl", "873-111-22-33"],
      ["M1 · I p.", "Piotr Zieliński", "os", "p.zielinski@gmail.com", ""],
      ["M2 · I p.", "Agnieszka Wójcik", "os", "a.wojcik@onet.pl", ""],
      ["M3 · II p.", "Krzysztof Mazur", "os", "k.mazur@wp.pl", ""],
      ["M4 · II p.", "Ewa Kozłowska", "os", "ewa.k@gmail.com", ""],
      ["M5 · III p.", "Andrzej Jankowski", "os", "a.jankowski@interia.pl", ""],
      ["M6 · III p.", "Barbara Wojciechowska", "os", "b.woj@gmail.com", ""],
      ["M7 · poddasze", "Grzegorz Kwiatkowski", "os", "g.kwiat@wp.pl", ""],
    ],
    b3: Array.from({ length: 10 }, (_, i) => {
      const firms = ["Tech-Soft sp. z o.o.", "Studio Projektowe ARK", "Kancelaria Nowak", "MedConsult sp. z o.o.",
        "Greenpoint Sp.j.", "Logistima sp. z o.o.", "Audytor Plus", "Biuro Rachunkowe Saldo", "DataNet sp. z o.o.", "Reklama360"];
      return [`B${i + 1} · ${Math.floor(i / 3) + 1} p.`, firms[i], "firma", `kontakt@firma${i + 1}.pl`, `873-2${i}0-00-1${i}`];
    }),
    b4: [
      ["U1 · parter", "Apteka Pod Lipą", "firma", "apteka@podlipa.pl", "873-333-44-55"],
      ["U2 · parter", "Kwiaciarnia Stokrotka", "firma", "stokrotka@kwiaty.pl", "873-444-55-66"],
      ["M1 · I p.", "Halina Sikora", "os", "h.sikora@gmail.com", ""],
      ["M2 · I p.", "Janusz Baran", "os", "j.baran@wp.pl", ""],
      ["M3 · II p.", "Zofia Duda", "os", "z.duda@onet.pl", ""],
    ],
  };

  const meterStatusOverride = { "b2-1": "offline" }; // M-Bus na Długej 8 chwilowo offline

  const meters = [];
  const tenants = [];
  Object.keys(unitDefs).forEach((bid, bi) => {
    const base = [48201577, 49120030, 50330070, 51440010][bi];
    const whenPool = ["6 min temu", "8 min temu", "12 min temu", "15 min temu", "22 min temu", "1 godz temu"];
    unitDefs[bid].forEach((u, i) => {
      const [lokal, tenant, ttype, email, nip] = u;
      const seed = bi * 13 + i * 7 + 5;
      const key = `${bid}-${i}`;
      const status = meterStatusOverride[key] || (seed % 11 === 0 ? "est" : "ok");
      const reading = 900 + seed * 137 + (i % 3) * 1820;
      const meter = {
        id: `${bid}m${i}`,
        bid, building: shortName[bid],
        lokal,
        meterName: `M-Bus ${String(5 + i).padStart(2, "0")}`,
        serial: String(base + i),
        mbus: String(5 + i).padStart(2, "0"),
        kwh: fmt(reading + (reading % 1) + 0.34),
        when: whenPool[(seed) % whenPool.length],
        status,
        spark: spark(seed),
        tenant,
      };
      meters.push(meter);
      tenants.push({
        id: `${bid}t${i}`,
        bid, building: shortName[bid],
        name: tenant, type: ttype, email, nip,
        lokal: lokal.split(" · ")[0],
        meter: meter.meterName,
        active: status !== "offline",
        lastInvoice: ["FV/0" + (41 + bi * 3 + i) + "/05/2026"][0],
        paid: !(bi === 0 && i === 2) && !(bi === 2 && i === 4),
      });
    });
  });

  // ---- Invoices (varied statuses for filtering) ----
  const invSeed = [
    ["FV/041/05/2026", "Anna Kowalska", "U1 · Rynek 12", 177.0, "ready",   "2026-06-14"],
    ["FV/042/05/2026", "Firma XYZ sp. z o.o.", "U2 · Rynek 12", 1240.0, "ready", "2026-06-14"],
    ["— szkic —",      "Tomasz Lewandowski", "M1 · Rynek 12", 151.0, "draft", "2026-06-14"],
    ["FV/038/04/2026", "Katarzyna Nowak", "M2 · Rynek 12", 142.5, "sent",   "2026-05-14"],
    ["FV/031/03/2026", "Paweł Wiśniewski", "M3 · Rynek 12", 168.0, "paid",   "2026-04-14"],
    ["FV/029/03/2026", "Salon Fryzjerski Bella", "U1 · Długa 8", 204.3, "overdue", "2026-04-14"],
    ["FV/043/05/2026", "Piotr Zieliński", "M1 · Długa 8", 118.8, "ready",   "2026-06-14"],
    ["— szkic —",      "Agnieszka Wójcik", "M2 · Długa 8", 96.4, "draft",   "2026-06-14"],
    ["FV/044/05/2026", "Tech-Soft sp. z o.o.", "B1 · Plac Wolności 3", 1240.0, "ready", "2026-06-14"],
    ["FV/045/05/2026", "Studio Projektowe ARK", "B2 · Plac Wolności 3", 806.5, "ready", "2026-06-14"],
    ["FV/036/04/2026", "Kancelaria Nowak", "B3 · Plac Wolności 3", 415.0, "sent",  "2026-05-14"],
    ["FV/030/03/2026", "MedConsult sp. z o.o.", "B4 · Plac Wolności 3", 388.0, "overdue", "2026-04-14"],
    ["— szkic —",      "Apteka Pod Lipą", "U1 · Krakowska 45", 388.0, "draft", "2026-06-14"],
    ["FV/033/04/2026", "Kwiaciarnia Stokrotka", "U2 · Krakowska 45", 132.0, "paid", "2026-05-14"],
  ];

  function computeInvoice(kwh) {
    const lines = tariff.components.map((c) => {
      const qty = c.type === "per_kwh" ? kwh : 1;
      const net = Math.round((c.type === "per_kwh" ? kwh * c.price : c.price) * 100) / 100;
      return { label: c.name, qty, unit: c.type === "per_kwh" ? "kWh" : "mc", price: c.price, net, vat: c.vat };
    });
    const net = Math.round(lines.reduce((s, l) => s + l.net, 0) * 100) / 100;
    const vat = Math.round(lines.reduce((s, l) => s + l.net * l.vat / 100, 0) * 100) / 100;
    return { lines, net, vat, gross: Math.round((net + vat) * 100) / 100 };
  }
  const money = (n) => n.toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const invoices = invSeed.map((r, i) => {
    const [no, tenant, lokal, kwh, status, due] = r;
    const calc = computeInvoice(kwh);
    return {
      id: "inv" + i, no, tenant, lokal, kwh,
      kwhStr: kwh.toLocaleString("pl-PL", { minimumFractionDigits: 1, maximumFractionDigits: 1 }),
      status, due,
      period: no.includes("05") ? "01–31.05.2026" : no.includes("04") ? "01–30.04.2026" : "01–31.03.2026",
      net: calc.net, vat: calc.vat, gross: calc.gross, lines: calc.lines,
    };
  });

  // dashboard "recent readings" = first reading of several buildings
  const readings = meters.filter((m, i) => [0, 1, 2, 9, 12, 17, 18, 27].includes(i)).map((m) => ({
    meter: m.meterName, serial: m.serial, lokal: m.lokal, bld: m.building, kwh: m.kwh, when: m.when, status: m.status,
  }));

  return {
    org, nav, tariff, buildings, shortName, meters, tenants, invoices, readings, money, computeInvoice,
    stats: { buildings: 4, metersOnline: "31 / 32", invoicesToSend: 15, overdue: 2 },
    attention: [
      { kind: "send", count: 15, title: "faktur gotowych do wysłania", note: "okres: maj 2026", cta: "Wyślij wszystkie" },
      { kind: "overdue", count: 2, title: "zaległe płatności", note: "łącznie 396,12 zł po terminie", cta: "Zobacz najemców" },
      { kind: "estimate", count: 1, title: "licznik offline", note: "M-Bus 06 · Długa 8 — brak danych z gateway", cta: "Sprawdź licznik" },
    ],
    invoicesMore: 7,
  };
})();
