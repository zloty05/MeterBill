import { useState } from "react";
import { getBuilding, listBuildings, listMeters, listTenants } from "../api/endpoints";
import type { BuildingOut } from "../api/types";
import { ModalBudynek } from "../components/modals/ModalBudynek";
import { Icon } from "../components/shared/Icon";
import { Pill } from "../components/shared/Pill";
import { useAsync } from "../lib/useAsync";

type Tab = "liczniki" | "najemcy" | "historia";

export function Budynki() {
  const [sel, setSel] = useState<string | null>(null);
  const [modal, setModal] = useState<{ open: boolean; data: BuildingOut | null }>({
    open: false,
    data: null,
  });

  const list = useAsync(() => listBuildings(), []);

  if (sel) {
    return (
      <>
        <BuildingDetail
          buildingId={sel}
          onBack={() => setSel(null)}
          onEdit={(b) => setModal({ open: true, data: b })}
        />
        <ModalBudynek
          open={modal.open}
          initial={modal.data}
          onClose={() => setModal({ open: false, data: null })}
          onSaved={list.reload}
        />
      </>
    );
  }

  return (
    <div className="content">
      <div className="page-h" style={{ alignItems: "center" }}>
        Budynki{" "}
        <small>· {list.data?.length ?? 0} obiektów · kliknij wiersz aby zobaczyć szczegóły</small>
        <span style={{ flex: 1 }} />
        <button className="btn primary" type="button" onClick={() => setModal({ open: true, data: null })}>
          <Icon name="plus" size={15} /> Dodaj budynek
        </button>
      </div>

      <div className="card sketch">
        {list.error ? (
          <div className="empty-hint">Nie udało się wczytać budynków: {list.error}</div>
        ) : list.loading || !list.data ? (
          <div className="empty-hint">Wczytywanie…</div>
        ) : list.data.length === 0 ? (
          <div className="empty-hint">Brak budynków. Dodaj pierwszy budynek przyciskiem powyżej.</div>
        ) : (
          <table className="wf">
            <thead>
              <tr>
                <th>Budynek</th>
                <th>PPE główne</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {list.data.map((b) => (
                <tr key={b.id} className="clickrow" onClick={() => setSel(b.id)}>
                  <td>
                    <div className="cell-strong">{b.name}</div>
                    <div className="cell-sub">{b.address}</div>
                  </td>
                  <td className="mono">{b.main_meter_ppe || "—"}</td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", alignItems: "center" }}>
                      <button
                        className="btn sm ghost"
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setModal({ open: true, data: b });
                        }}
                      >
                        Edytuj
                      </button>
                      <span className="chev">
                        <Icon name="arrow" size={16} />
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ModalBudynek
        open={modal.open}
        initial={modal.data}
        onClose={() => setModal({ open: false, data: null })}
        onSaved={list.reload}
      />
    </div>
  );
}

function BuildingDetail({
  buildingId,
  onBack,
  onEdit,
}: {
  buildingId: string;
  onBack: () => void;
  onEdit: (b: BuildingOut) => void;
}) {
  const [tab, setTab] = useState<Tab>("liczniki");

  const detail = useAsync(
    () => Promise.all([getBuilding(buildingId), listMeters(buildingId), listTenants(buildingId)]),
    [buildingId]
  );

  return (
    <div className="content">
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div className="backlink" onClick={onBack}>
          ← Wszystkie budynki
        </div>
        <span style={{ flex: 1 }} />
        {detail.data && (
          <button className="btn sm ghost" type="button" onClick={() => onEdit(detail.data![0])}>
            Edytuj budynek
          </button>
        )}
      </div>

      {detail.error ? (
        <div className="card sketch">
          <div className="empty-hint">Nie udało się wczytać budynku: {detail.error}</div>
        </div>
      ) : detail.loading || !detail.data ? (
        <div className="card sketch">
          <div className="empty-hint">Wczytywanie…</div>
        </div>
      ) : (
        (() => {
          const [b, meters, tenants] = detail.data;
          return (
            <>
              <div className="page-h" style={{ marginTop: 2 }}>
                {b.name} <small>· {b.address}</small>
              </div>
              <div className="card sketch" style={{ padding: 0 }}>
                <div className="meta-strip">
                  <div className="mi">
                    <div className="k">PPE główne</div>
                    <div className="v" style={{ fontFamily: "var(--mono)", fontSize: 13 }}>
                      {b.main_meter_ppe || "—"}
                    </div>
                  </div>
                  <div className="mi">
                    <div className="k">Liczniki</div>
                    <div className="v green">{meters.length}</div>
                  </div>
                  <div className="mi">
                    <div className="k">Najemcy</div>
                    <div className="v">{tenants.length}</div>
                  </div>
                </div>

                <div className="tabs">
                  <button
                    className={"tab" + (tab === "liczniki" ? " on" : "")}
                    onClick={() => setTab("liczniki")}
                  >
                    <Icon name="gauge" size={15} /> Liczniki <span className="badge">{meters.length}</span>
                  </button>
                  <button
                    className={"tab" + (tab === "najemcy" ? " on" : "")}
                    onClick={() => setTab("najemcy")}
                  >
                    <Icon name="users" size={15} /> Najemcy <span className="badge">{tenants.length}</span>
                  </button>
                  <button
                    className={"tab" + (tab === "historia" ? " on" : "")}
                    onClick={() => setTab("historia")}
                  >
                    <Icon name="doc" size={15} /> Historia
                  </button>
                </div>

                {tab === "liczniki" &&
                  (meters.length === 0 ? (
                    <div className="empty-hint">Brak liczników w tym budynku.</div>
                  ) : (
                    <div style={{ padding: "4px var(--pad) var(--pad)" }}>
                      <table className="wf">
                        <thead>
                          <tr>
                            <th>Lokal</th>
                            <th>Nr seryjny / M-Bus</th>
                            <th>Protokół</th>
                            <th>Grupa</th>
                            <th>PPE</th>
                          </tr>
                        </thead>
                        <tbody>
                          {meters.map((m) => (
                            <tr key={m.id}>
                              <td className="cell-strong">{m.label || "—"}</td>
                              <td>
                                <div className="mono">{m.serial_no}</div>
                                <div className="cell-sub">adr {m.mbus_address || "—"}</div>
                              </td>
                              <td className="cell-sub">{m.protocol}</td>
                              <td className="cell-sub">{m.tariff_group}</td>
                              <td className="mono">{m.ppe_code || "—"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}

                {tab === "najemcy" &&
                  (tenants.length === 0 ? (
                    <div className="empty-hint">Brak najemców w tym budynku.</div>
                  ) : (
                    <div style={{ padding: "4px var(--pad) var(--pad)" }}>
                      <table className="wf">
                        <thead>
                          <tr>
                            <th>Lokal</th>
                            <th>Najemca</th>
                            <th>Typ</th>
                            <th>E-mail</th>
                            <th>NIP</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tenants.map((t) => (
                            <tr key={t.id}>
                              <td className="cell-strong">{t.unit_no}</td>
                              <td>{t.name}</td>
                              <td>
                                <span className="pill draft">
                                  <span className="dot" />
                                  {t.nip ? "firma · VAT" : "os. fizyczna"}
                                </span>
                              </td>
                              <td className="cell-sub">{t.email}</td>
                              <td className="mono">{t.nip || "—"}</td>
                              <td>
                                <Pill status={t.active ? "online" : "offline"} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}

                {tab === "historia" && (
                  <div className="empty-hint">
                    Historia zdarzeń budynku — w przygotowaniu (brak endpointu w tym etapie).
                  </div>
                )}
              </div>
            </>
          );
        })()
      )}
    </div>
  );
}
