import type { BuildingOut, InvoiceOut, MeterOut, TenantOut } from "../api/types";

// Agregaty których backend listowy nie zwraca — liczymy je na froncie z list.
// Czego NIE da się policzyć z obecnego API (np. status online/offline licznika,
// kWh/mc per budynek) → zwracamy null i UI pokazuje "—" (nie zmyślamy).

export type BuildingStats = {
  metersTotal: number;
  tenantsCount: number;
  toSend: number; // faktury ready
  overdue: number; // faktury overdue
};

/** Mapa building_id → statystyki, z globalnych list. */
export function buildBuildingStats(
  buildings: BuildingOut[],
  meters: MeterOut[],
  tenants: TenantOut[],
  invoices: InvoiceOut[]
): Map<string, BuildingStats> {
  // tenant_id → building_id (faktury mają tenant_id, nie building_id)
  const tenantBuilding = new Map<string, string>();
  for (const t of tenants) tenantBuilding.set(t.id, t.building_id);

  const stats = new Map<string, BuildingStats>();
  for (const b of buildings) {
    stats.set(b.id, { metersTotal: 0, tenantsCount: 0, toSend: 0, overdue: 0 });
  }
  for (const m of meters) {
    const s = stats.get(m.building_id);
    if (s) s.metersTotal += 1;
  }
  for (const t of tenants) {
    const s = stats.get(t.building_id);
    if (s) s.tenantsCount += 1;
  }
  for (const inv of invoices) {
    const bid = tenantBuilding.get(inv.tenant_id);
    if (!bid) continue;
    const s = stats.get(bid);
    if (!s) continue;
    if (inv.status === "ready") s.toSend += 1;
    if (inv.status === "overdue") s.overdue += 1;
  }
  return stats;
}

export type GlobalStats = {
  buildings: number;
  metersTotal: number;
  invoicesToSend: number;
  overdue: number;
};

export function buildGlobalStats(
  buildings: BuildingOut[],
  meters: MeterOut[],
  invoices: InvoiceOut[]
): GlobalStats {
  return {
    buildings: buildings.length,
    metersTotal: meters.length,
    invoicesToSend: invoices.filter((i) => i.status === "ready").length,
    overdue: invoices.filter((i) => i.status === "overdue").length,
  };
}
