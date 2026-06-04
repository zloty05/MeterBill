import { listBuildings, listInvoices, listMeters, listTenants } from "../api/endpoints";
import { BuildingTile } from "../components/dashboard/BuildingTile";
import { StatCards, type StatCard } from "../components/shared/StatCards";
import { buildBuildingStats, buildGlobalStats } from "../lib/aggregates";
import { useAsync } from "../lib/useAsync";

export function Dashboard({ onOpenBuildings }: { onOpenBuildings?: () => void }) {
  const { data, loading, error } = useAsync(
    () => Promise.all([listBuildings(), listMeters(), listTenants(), listInvoices()]),
    []
  );

  if (error) {
    return (
      <div className="content">
        <div className="page-h hand-title">Dashboard</div>
        <div className="card sketch">
          <div className="empty-hint">Nie udało się wczytać danych: {error}</div>
        </div>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="content">
        <div className="page-h hand-title">Dashboard</div>
        <div className="card sketch">
          <div className="empty-hint">Wczytywanie…</div>
        </div>
      </div>
    );
  }

  const [buildings, meters, tenants, invoices] = data;
  const global = buildGlobalStats(buildings, meters, invoices);
  const perBuilding = buildBuildingStats(buildings, meters, tenants, invoices);

  const cards: StatCard[] = [
    { tone: "", label: "Aktywne budynki", num: global.buildings, sub: "wszystkie monitorowane", icon: "building" },
    { tone: "accent", label: "Liczniki", num: global.metersTotal, sub: "M-Bus · odczyt co 15 min", icon: "gauge" },
    { tone: "", label: "Faktury do wysłania", num: global.invoicesToSend, sub: "status: gotowe", icon: "doc" },
    { tone: "danger", label: "Zaległe płatności", num: global.overdue, sub: "po terminie", icon: "bell" },
  ];

  return (
    <div className="content">
      <div className="page-h hand-title">
        Budynki <small>· kliknij budynek aby zobaczyć liczniki i najemców</small>
      </div>
      <StatCards cards={cards} />
      {buildings.length === 0 ? (
        <div className="card sketch">
          <div className="empty-hint">Brak budynków. Dodaj pierwszy budynek w zakładce „Budynki".</div>
        </div>
      ) : (
        <div className="bld-grid">
          {buildings.map((b) => (
            <BuildingTile key={b.id} b={b} stats={perBuilding.get(b.id)} onOpen={onOpenBuildings} />
          ))}
        </div>
      )}
    </div>
  );
}
