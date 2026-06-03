/* global React, Icon, Pill, Cbx, ModalTaryfa */
const { useState: useS2 } = React;

/* ============ Faktury ============ */
const STATUS_FILTERS = [
  { id: "all",     label: "Wszystkie" },
  { id: "draft",   label: "Szkice" },
  { id: "ready",   label: "Gotowe" },
  { id: "sent",    label: "Wysłane" },
  { id: "paid",    label: "Opłacone" },
  { id: "overdue", label: "Po terminie" },
];

function InvoiceDrawer({ inv, onClose }) {
  const open   = !!inv;
  const tenant = inv ? WF.tenants.find((t) => t.name === inv.tenant) : null;
  return (
    <>
      <div className={"drawer-overlay" + (open ? " open" : "")} onClick={onClose} />
      <div className={"drawer" + (open ? " open" : "")}>
        {inv && (
          <>
            <div className="drawer-head">
              <div>
                <div className="cell-sub" style={{ fontFamily: "var(--mono)" }}>{inv.no}</div>
                <div style={{ fontWeight: 700, fontSize: 18, marginTop: 2 }}>{inv.tenant}</div>
                <div style={{ marginTop: 6 }}><Pill status={inv.status} /></div>
              </div>
              <button className="x" onClick={onClose}><Icon name="x" size={16} /></button>
            </div>
            <div className="drawer-body">
              <div className="party-grid">
                <div className="party">
                  <div className="role">Sprzedawca</div>
                  <div className="nm">{WF.org.name}</div>
                  <div className="meta">NIP 873-100-00-00<br />ul. Wałowa 2, 33-100 Tarnów</div>
                </div>
                <div className="party">
                  <div className="role">Nabywca</div>
                  <div className="nm">{inv.tenant}</div>
                  <div className="meta">{tenant && tenant.nip ? "NIP " + tenant.nip : "osoba fizyczna"}<br />{inv.lokal}</div>
                </div>
              </div>
              <div>
                <div className="kv"><span className="k">Okres rozliczeniowy</span><span className="v">{inv.period}</span></div>
                <div className="kv"><span className="k">Zużycie energii</span><span className="v">{inv.kwhStr} kWh</span></div>
                <div className="kv"><span className="k">Termin płatności</span><span className="v">{inv.due}</span></div>
              </div>
              <div className="card sketch" style={{ boxShadow: "none" }}>
                <table className="wf">
                  <thead><tr><th>Pozycja</th><th style={{ textAlign: "right" }}>Ilość</th><th style={{ textAlign: "right" }}>Cena</th><th style={{ textAlign: "right" }}>Netto</th></tr></thead>
                  <tbody>
                    {inv.lines.map((l, i) => (
                      <tr key={i}>
                        <td style={{ fontSize: 13 }}>{l.label}</td>
                        <td className="num-cell" style={{ textAlign: "right" }}>{l.qty.toLocaleString("pl-PL", { maximumFractionDigits: 1 })} {l.unit}</td>
                        <td className="num-cell" style={{ textAlign: "right" }}>{l.price.toLocaleString("pl-PL", { minimumFractionDigits: l.unit === "kWh" ? 4 : 2 })}</td>
                        <td className="num-cell" style={{ textAlign: "right" }}>{WF.money(l.net)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <div className="sumrow"><span>Razem netto</span><span className="v">{WF.money(inv.net)} zł</span></div>
                <div className="sumrow"><span>VAT 23%</span><span className="v">{WF.money(inv.vat)} zł</span></div>
                <div className="sumrow total"><span>Razem brutto</span><span className="v">{WF.money(inv.gross)} zł</span></div>
              </div>
              <div className="party" style={{ background: "var(--accent-soft)", borderColor: "var(--accent-line)" }}>
                <div className="role">Do zapłaty</div>
                <div className="nm" style={{ fontSize: 17 }}>{WF.money(inv.gross)} zł</div>
                <div className="meta">nr konta: 12 1140 0000 0000 0000 1234 5678<br />tytuł: {inv.no}</div>
              </div>
            </div>
            <div className="drawer-foot">
              <button className="btn ghost" style={{ flex: 1 }}><Icon name="doc" size={15} /> Podgląd PDF</button>
              {inv.status === "draft"
                ? <button className="btn primary" style={{ flex: 1 }}><Icon name="plus" size={15} /> Generuj fakturę</button>
                : <button className="btn primary" style={{ flex: 1 }}><Icon name="arrow" size={15} /> Wyślij e-mailem</button>}
            </div>
          </>
        )}
      </div>
    </>
  );
}

function ScreenFaktury() {
  const [filter, setFilter] = useS2("all");
  const [sel,    setSel]    = useS2(() => new Set());
  const [open,   setOpen]   = useS2(null);

  const counts = {};
  WF.invoices.forEach((i) => { counts[i.status] = (counts[i.status] || 0) + 1; });
  const rows = WF.invoices.filter((i) => filter === "all" || i.status === filter);

  const toggle    = (id) => { const n = new Set(sel); n.has(id) ? n.delete(id) : n.add(id); setSel(n); };
  const allOn     = rows.length > 0 && rows.every((r) => sel.has(r.id));
  const toggleAll = () => { const n = new Set(sel); allOn ? rows.forEach((r) => n.delete(r.id)) : rows.forEach((r) => n.add(r.id)); setSel(n); };
  const selRows   = WF.invoices.filter((i) => sel.has(i.id));
  const draftSel  = selRows.filter((i) => i.status === "draft").length;
  const readySel  = selRows.filter((i) => i.status === "ready").length;

  return (
    <div className="content">
      <div className="page-h">Faktury <small>· {WF.invoices.length} dokumentów · okres bieżący i archiwum</small></div>
      <div className="card sketch" style={{ padding: 0 }}>
        <div className="filterbar">
          <div className="chips">
            {STATUS_FILTERS.map((f) => (
              <button key={f.id} className={"chip" + (filter === f.id ? " on" : "")} onClick={() => setFilter(f.id)}>
                {f.label}<span className="cnt">{f.id === "all" ? WF.invoices.length : (counts[f.id] || 0)}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="bulk-bar">
          <Cbx on={allOn} onClick={toggleAll} />
          <span>Zaznaczono <b>{sel.size}</b></span>
          <div className="spacer" />
          <button className="btn sm" disabled={!draftSel}><Icon name="plus" size={14} /> Generuj zaznaczone ({draftSel})</button>
          <button className="btn primary sm" disabled={!readySel}><Icon name="arrow" size={14} /> Wyślij zaznaczone ({readySel})</button>
        </div>
        <div style={{ padding: "4px var(--pad) var(--pad)" }}>
          <table className="wf">
            <thead>
              <tr><th style={{ width: 28 }}></th><th>Nr faktury</th><th>Najemca</th><th>Lokal</th><th>Okres</th><th style={{ textAlign: "right" }}>kWh</th><th style={{ textAlign: "right" }}>Brutto</th><th>Status</th><th>Termin</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="clickrow" onClick={() => setOpen(r)}>
                  <td onClick={(e) => { e.stopPropagation(); toggle(r.id); }}><Cbx on={sel.has(r.id)} onClick={() => {}} /></td>
                  <td className="mono">{r.no}</td>
                  <td className="cell-strong">{r.tenant}</td>
                  <td className="cell-sub">{r.lokal}</td>
                  <td className="cell-sub">{r.period}</td>
                  <td className="num-cell" style={{ textAlign: "right" }}>{r.kwhStr}</td>
                  <td className="num-cell" style={{ textAlign: "right" }}>{WF.money(r.gross)} zł</td>
                  <td><Pill status={r.status} /></td>
                  <td className="cell-sub">{r.due}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && (
            <div className="empty-hint">Brak faktur o statusie „{STATUS_FILTERS.find((f) => f.id === filter) && STATUS_FILTERS.find((f) => f.id === filter).label}".</div>
          )}
        </div>
      </div>
      <InvoiceDrawer inv={open} onClose={() => setOpen(null)} />
    </div>
  );
}

/* ============ Taryfy ============ */
function ScreenTaryfy() {
  const [rows,   setRows]   = useS2(() => WF.tariff.components.map((c, i) => ({ ...c, _id: i })));
  const [nextId, setNextId] = useS2(WF.tariff.components.length);
  const [tModal, setTModal] = useS2(false);

  const upd    = (id, key, val) => setRows((rs) => rs.map((r) => r._id === id ? { ...r, [key]: val } : r));
  const del    = (id)           => setRows((rs) => rs.filter((r) => r._id !== id));
  const add    = ()             => { setRows((rs) => [...rs, { _id: nextId, name: "Nowy składnik", type: "per_kwh", price: 0, unit: "zł/kWh", vat: 23 }]); setNextId((n) => n + 1); };

  const sumKwh   = rows.filter((r) => r.type === "per_kwh").reduce((s, r) => s + (+r.price || 0), 0);
  const sumFixed = rows.filter((r) => r.type === "monthly_fixed").reduce((s, r) => s + (+r.price || 0), 0);
  const brutto   = (r) => (+r.price || 0) * (1 + (+r.vat || 0) / 100);

  return (
    <div className="content">
      <div className="page-h">Taryfy <small>· szablon na podstawie faktury dystrybutora</small></div>
      <div className="card sketch" style={{ padding: 0 }}>
        <div className="card-head">
          <h3>{WF.tariff.name}</h3>
          <span className="pill ok" style={{ borderRadius: "var(--r-pill)" }}><span className="dot" />aktywna</span>
          <div className="spacer" />
          <button className="btn primary sm" onClick={() => setTModal(true)}>
            <Icon name="plus" size={14} /> Dodaj taryfę
          </button>
          <button className="btn sm ghost"><Icon name="doc" size={14} /> Źródło: {WF.tariff.source}</button>
        </div>
        <div className="meta-strip">
          <div className="mi"><div className="k">Grupa taryfowa</div><div className="v">{WF.tariff.group}</div></div>
          <div className="mi"><div className="k">VAT domyślny</div><div className="v">{WF.tariff.vat}%</div></div>
          <div className="mi"><div className="k">Marża zarządcy</div><div className="v">{WF.tariff.margin}%</div></div>
          <div className="mi"><div className="k">Obowiązuje od</div><div className="v">{WF.tariff.validFrom}</div></div>
          <div className="mi"><div className="k">Suma zmienna</div><div className="v green">{sumKwh.toLocaleString("pl-PL", { minimumFractionDigits: 4 })} zł/kWh</div></div>
          <div className="mi"><div className="k">Suma stała</div><div className="v green">{sumFixed.toLocaleString("pl-PL", { minimumFractionDigits: 2 })} zł/mc</div></div>
        </div>
        <div style={{ padding: "4px var(--pad) var(--pad)" }}>
          <table className="wf">
            <thead>
              <tr>
                <th style={{ width: "34%" }}>Nazwa składnika</th><th>Typ</th>
                <th style={{ textAlign: "right" }}>Cena netto</th>
                <th style={{ textAlign: "right", width: 80 }}>VAT %</th>
                <th style={{ textAlign: "right" }}>Cena brutto</th>
                <th style={{ width: 34 }}></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r._id}>
                  <td><input className="tin txt" value={r.name} onChange={(e) => upd(r._id, "name", e.target.value)} /></td>
                  <td>
                    <select className="tin sel" value={r.type} onChange={(e) => upd(r._id, "type", e.target.value)}>
                      <option value="per_kwh">per_kwh</option>
                      <option value="monthly_fixed">monthly_fixed</option>
                    </select>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
                      <input className="tin" style={{ maxWidth: 96 }} value={r.price} onChange={(e) => upd(r._id, "price", e.target.value)} />
                      <span className="cell-sub" style={{ minWidth: 46 }}>{r.type === "per_kwh" ? "zł/kWh" : "zł/mc"}</span>
                    </div>
                  </td>
                  <td style={{ textAlign: "right" }}><input className="tin" style={{ maxWidth: 56 }} value={r.vat} onChange={(e) => upd(r._id, "vat", e.target.value)} /></td>
                  <td className="num-cell" style={{ textAlign: "right" }}>{brutto(r).toLocaleString("pl-PL", { minimumFractionDigits: r.type === "per_kwh" ? 4 : 2 })}</td>
                  <td style={{ textAlign: "center" }}><button className="row-del" onClick={() => del(r._id)} title="Usuń składnik"><Icon name="trash" size={15} /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: "14px 4px 2px" }}>
            <button className="btn" onClick={add}><Icon name="plus" size={15} /> Dodaj składnik</button>
          </div>
        </div>
      </div>

      <ModalTaryfa
        open={tModal}
        onClose={() => setTModal(false)}
        onSave={(d) => console.log("taryfa →", d)}
      />
    </div>
  );
}

Object.assign(window, { ScreenFaktury, ScreenTaryfy, InvoiceDrawer });
