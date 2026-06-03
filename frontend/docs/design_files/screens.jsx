/* global React, Icon, Pill, Sparkline, ModalBudynek, ModalLicznik, ModalNajemca */
const { useState: useS } = React;

/* ============ SparkCell ============ */
function SparkCell({ data }) {
  const up = data[data.length - 1] >= data[0];
  const pct = Math.round(Math.abs((data[data.length - 1] - data[0]) / (data[0] || 1)) * 100);
  return (
    <div className="spark-cell">
      <Sparkline data={data} color="auto" />
      <span className={"spark-delta " + (up ? "up" : "down")}>{up ? "▲" : "▼"}{pct}%</span>
    </div>
  );
}

/* ============ Budynki ============ */
const BLD_HISTORY = [
  { dot: "",    t: "Wysłano 5 faktur za maj 2026",          d: "Resend · 5/5 dostarczonych",              when: "01.06 · 09:12" },
  { dot: "",    t: "Wygenerowano faktury (okres maj)",       d: "Silnik taryfowy G11 · 9 lokali",          when: "01.06 · 09:05" },
  { dot: "red", t: "Płatność po terminie — Salon Bella",    d: "FV/029/03/2026 · 211,77 zł",              when: "29.05 · 00:00" },
  { dot: "gray",t: "Odczyt zbiorczy M-Bus (9 liczników)",   d: "Gateway WAGO PFC300 · remote",            when: "31.05 · 23:50" },
  { dot: "gray",t: "Dodano najemcę: Firma XYZ sp. z o.o.", d: "Lokal U2 · faktura VAT",                  when: "12.05 · 14:20" },
];

function ScreenBudynki() {
  const [sel, setSel]     = useS(null);
  const [tab, setTab]     = useS("liczniki");
  const [bModal, setBModal] = useS({ open: false, data: null });
  const [mModal, setMModal] = useS({ open: false, data: null });
  const [nModal, setNModal] = useS({ open: false, data: null });

  const b        = WF.buildings.find((x) => x.id === sel);
  const bMeters  = b ? WF.meters.filter((m) => m.bid === b.id)  : [];
  const bTenants = b ? WF.tenants.filter((t) => t.bid === b.id) : [];

  return (
    <div className="content">
      {!b ? (
        /* ── Lista budynków ── */
        <>
          <div className="page-h" style={{ alignItems: "center" }}>
            Budynki <small>· {WF.buildings.length} obiektów · kliknij wiersz aby zobaczyć szczegóły</small>
            <span style={{ flex: 1 }} />
            <button className="btn primary" onClick={() => setBModal({ open: true, data: null })}>
              <Icon name="plus" size={15} /> Dodaj budynek
            </button>
          </div>
          <div className="card sketch">
            <table className="wf">
              <thead>
                <tr>
                  <th>Budynek</th><th>Taryfa</th>
                  <th style={{ textAlign: "center" }}>Liczniki</th>
                  <th style={{ textAlign: "center" }}>Najemcy</th>
                  <th style={{ textAlign: "center" }}>Do wysłania</th>
                  <th style={{ textAlign: "center" }}>Zaległe</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {WF.buildings.map((x) => (
                  <tr key={x.id} className="clickrow" onClick={() => { setSel(x.id); setTab("liczniki"); }}>
                    <td><div className="cell-strong">{x.name}</div><div className="cell-sub">{x.addr} · PPE {x.ppe}</div></td>
                    <td><span className="pill ok"><span className="dot" />G11</span></td>
                    <td style={{ textAlign: "center" }}><span className="num-cell">{x.online}/{x.meters}</span></td>
                    <td style={{ textAlign: "center" }}><span className="num-cell">{x.tenants}</span></td>
                    <td style={{ textAlign: "center" }}><span className="num-cell">{x.toSend}</span></td>
                    <td style={{ textAlign: "center" }}>
                      {x.overdue > 0
                        ? <span className="num-cell" style={{ color: "var(--danger)" }}>{x.overdue}</span>
                        : <span className="cell-sub">—</span>}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", alignItems: "center" }}>
                        <button className="btn sm ghost" onClick={(e) => { e.stopPropagation(); setBModal({ open: true, data: x }); }}>Edytuj</button>
                        <span className="chev"><Icon name="arrow" size={16} /></span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        /* ── Szczegóły budynku ── */
        <>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div className="backlink" onClick={() => setSel(null)}>← Wszystkie budynki</div>
            <span style={{ flex: 1 }} />
            <button className="btn sm ghost" onClick={() => setBModal({ open: true, data: b })}>Edytuj budynek</button>
          </div>
          <div className="page-h" style={{ marginTop: 2 }}>{b.name} <small>· {b.addr}</small></div>
          <div className="card sketch" style={{ padding: 0 }}>
            <div className="meta-strip">
              <div className="mi"><div className="k">Taryfa</div><div className="v">G11 – ZAEL 2026</div></div>
              <div className="mi"><div className="k">PPE główne</div><div className="v" style={{ fontFamily: "var(--mono)", fontSize: 13 }}>{b.ppe}</div></div>
              <div className="mi"><div className="k">Liczniki online</div><div className="v green">{b.online} / {b.meters}</div></div>
              <div className="mi"><div className="k">Najemcy</div><div className="v">{b.tenants}</div></div>
              <div className="mi"><div className="k">Faktury do wysłania</div><div className="v">{b.toSend}</div></div>
              <div className="mi"><div className="k">Zużycie / mc</div><div className="v">{b.kwh} kWh</div></div>
            </div>

            <div className="tabs">
              <button className={"tab" + (tab === "liczniki" ? " on" : "")} onClick={() => setTab("liczniki")}><Icon name="gauge" size={15} /> Liczniki <span className="badge">{bMeters.length}</span></button>
              <button className={"tab" + (tab === "najemcy" ? " on" : "")} onClick={() => setTab("najemcy")}><Icon name="users" size={15} /> Najemcy <span className="badge">{bTenants.length}</span></button>
              <button className={"tab" + (tab === "historia" ? " on" : "")} onClick={() => setTab("historia")}><Icon name="doc" size={15} /> Historia</button>
              <span style={{ flex: 1 }} />
              {tab === "liczniki" && (
                <button className="btn sm" style={{ alignSelf: "center", marginRight: "var(--pad)", marginBottom: 3 }}
                  onClick={() => setMModal({ open: true, data: null })}>
                  <Icon name="plus" size={14} /> Dodaj licznik
                </button>
              )}
              {tab === "najemcy" && (
                <button className="btn sm" style={{ alignSelf: "center", marginRight: "var(--pad)", marginBottom: 3 }}
                  onClick={() => setNModal({ open: true, data: null })}>
                  <Icon name="plus" size={14} /> Dodaj najemcę
                </button>
              )}
            </div>

            {tab === "liczniki" && (
              <div style={{ padding: "4px var(--pad) var(--pad)" }}>
                <table className="wf">
                  <thead><tr><th>Lokal</th><th>Licznik / SN</th><th style={{ textAlign: "right" }}>Ostatni odczyt</th><th>Kiedy</th><th>Status</th><th>Trend 10 mc</th><th></th></tr></thead>
                  <tbody>
                    {bMeters.map((m) => (
                      <tr key={m.id}>
                        <td className="cell-strong">{m.lokal}</td>
                        <td><div>{m.meterName}</div><div className="mono">SN {m.serial} · adr {m.mbus}</div></td>
                        <td className="num-cell" style={{ textAlign: "right" }}>{m.kwh} <span className="cell-sub">kWh</span></td>
                        <td className="cell-sub">{m.when}</td>
                        <td><Pill status={m.status === "ok" ? "online" : m.status} /></td>
                        <td><SparkCell data={m.spark} /></td>
                        <td style={{ textAlign: "right" }}>
                          <button className="btn sm ghost" onClick={() => setMModal({ open: true, data: m })}>Edytuj</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {tab === "najemcy" && (
              <div style={{ padding: "4px var(--pad) var(--pad)" }}>
                <table className="wf">
                  <thead><tr><th>Lokal</th><th>Najemca</th><th>Typ</th><th>E-mail</th><th>NIP</th><th>Licznik</th><th>Status</th><th></th></tr></thead>
                  <tbody>
                    {bTenants.map((t) => (
                      <tr key={t.id}>
                        <td className="cell-strong">{t.lokal}</td>
                        <td>{t.name}</td>
                        <td><span className="pill draft" style={{ borderRadius: "var(--r-pill)" }}><span className="dot" />{t.type === "firma" ? "firma · VAT" : "os. fizyczna"}</span></td>
                        <td className="cell-sub">{t.email}</td>
                        <td className="mono">{t.nip || "—"}</td>
                        <td className="mono">{t.meter}</td>
                        <td><Pill status={t.active ? "online" : "offline"} /></td>
                        <td style={{ textAlign: "right" }}>
                          <button className="btn sm ghost" onClick={() => setNModal({ open: true, data: t })}>Edytuj</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {tab === "historia" && (
              <div className="tl">
                {BLD_HISTORY.map((h, i) => (
                  <div key={i} className="tl-item">
                    <div className={"tl-dot " + h.dot} />
                    <div className="tl-main"><div className="t">{h.t}</div><div className="d">{h.d}</div></div>
                    <div className="tl-when">{h.when}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Modale ── */}
      <ModalBudynek
        open={bModal.open} initial={bModal.data}
        onClose={() => setBModal({ open: false, data: null })}
        onSave={(d) => console.log("budynek →", d)}
      />
      <ModalLicznik
        open={mModal.open} initial={mModal.data} buildingId={b ? b.id : null}
        onClose={() => setMModal({ open: false, data: null })}
        onSave={(d) => console.log("licznik →", d)}
      />
      <ModalNajemca
        open={nModal.open} initial={nModal.data} buildingId={b ? b.id : null}
        onClose={() => setNModal({ open: false, data: null })}
        onSave={(d) => console.log("najemca →", d)}
      />
    </div>
  );
}

/* ============ Liczniki ============ */
function ScreenLiczniki() {
  const [bid, setBid]     = useS("all");
  const [mModal, setMModal] = useS({ open: false, data: null });
  const rows = WF.meters.filter((m) => bid === "all" || m.bid === bid);

  return (
    <div className="content">
      <div className="page-h" style={{ alignItems: "center" }}>
        Liczniki <small>· {rows.length} podliczników M-Bus · odczyt co 15 min</small>
        <span style={{ flex: 1 }} />
        <button className="btn primary" onClick={() => setMModal({ open: true, data: null })}>
          <Icon name="plus" size={15} /> Dodaj licznik
        </button>
      </div>
      <div className="card sketch" style={{ padding: 0 }}>
        <div className="filterbar">
          <span className="lbl">Budynek:</span>
          <select className="sel" value={bid} onChange={(e) => setBid(e.target.value)}>
            <option value="all">Wszystkie budynki ({WF.meters.length})</option>
            {WF.buildings.map((b) => <option key={b.id} value={b.id}>{b.name} ({b.meters})</option>)}
          </select>
          <div style={{ flex: 1 }} />
          <span className="pill online" style={{ borderRadius: "var(--r-pill)" }}><span className="dot" />{WF.meters.filter((m) => m.status !== "offline").length} online</span>
          <span className="pill offline" style={{ borderRadius: "var(--r-pill)" }}><span className="dot" />{WF.meters.filter((m) => m.status === "offline").length} offline</span>
        </div>
        <div style={{ padding: "4px var(--pad) var(--pad)" }}>
          <table className="wf">
            <thead>
              <tr><th>Lokal</th><th>Budynek</th><th>Nr seryjny M-Bus</th><th style={{ textAlign: "right" }}>Ostatni odczyt</th><th>Kiedy</th><th>Status</th><th>Trend 10 mc</th><th></th></tr>
            </thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.id}>
                  <td className="cell-strong">{m.lokal}</td>
                  <td className="cell-sub">{m.building}</td>
                  <td><div className="mono">{m.serial}</div><div className="cell-sub">{m.meterName} · adr {m.mbus}</div></td>
                  <td className="num-cell" style={{ textAlign: "right" }}>{m.kwh} <span className="cell-sub">kWh</span></td>
                  <td className="cell-sub">{m.when}</td>
                  <td><Pill status={m.status === "ok" ? "online" : m.status} /></td>
                  <td><SparkCell data={m.spark} /></td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn sm ghost" onClick={() => setMModal({ open: true, data: m })}>Edytuj</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <ModalLicznik
        open={mModal.open} initial={mModal.data} buildingId={bid !== "all" ? bid : null}
        onClose={() => setMModal({ open: false, data: null })}
        onSave={(d) => console.log("licznik →", d)}
      />
    </div>
  );
}

/* ============ Najemcy ============ */
function ScreenNajemcy() {
  const [bid, setBid]     = useS("all");
  const [nModal, setNModal] = useS({ open: false, data: null });
  const rows = WF.tenants.filter((t) => bid === "all" || t.bid === bid);

  return (
    <div className="content">
      <div className="page-h" style={{ alignItems: "center" }}>
        Najemcy <small>· {rows.length} aktywnych najemców</small>
        <span style={{ flex: 1 }} />
        <button className="btn primary" onClick={() => setNModal({ open: true, data: null })}>
          <Icon name="plus" size={15} /> Dodaj najemcę
        </button>
      </div>
      <div className="card sketch" style={{ padding: 0 }}>
        <div className="filterbar">
          <span className="lbl">Budynek:</span>
          <select className="sel" value={bid} onChange={(e) => setBid(e.target.value)}>
            <option value="all">Wszystkie budynki ({WF.tenants.length})</option>
            {WF.buildings.map((b) => <option key={b.id} value={b.id}>{b.name} ({b.tenants})</option>)}
          </select>
        </div>
        <div style={{ padding: "4px var(--pad) var(--pad)" }}>
          <table className="wf">
            <thead>
              <tr><th>Najemca</th><th>Budynek / lokal</th><th>Typ</th><th>E-mail</th><th>Ostatnia faktura</th><th>Płatność</th><th></th></tr>
            </thead>
            <tbody>
              {rows.map((t) => (
                <tr key={t.id}>
                  <td className="cell-strong">{t.name}</td>
                  <td className="cell-sub">{t.building} · {t.lokal}</td>
                  <td><span className="pill draft" style={{ borderRadius: "var(--r-pill)" }}><span className="dot" />{t.type === "firma" ? "firma · VAT" : "os. fizyczna"}</span></td>
                  <td className="cell-sub">{t.email}</td>
                  <td className="mono">{t.lastInvoice}</td>
                  <td><Pill status={t.paid ? "paid" : "overdue"} /></td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn sm ghost" onClick={() => setNModal({ open: true, data: t })}>Edytuj</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <ModalNajemca
        open={nModal.open} initial={nModal.data} buildingId={bid !== "all" ? bid : null}
        onClose={() => setNModal({ open: false, data: null })}
        onSave={(d) => console.log("najemca →", d)}
      />
    </div>
  );
}

Object.assign(window, { ScreenBudynki, ScreenLiczniki, ScreenNajemcy, SparkCell });
