import { apiFetch } from "./client";
import type {
  BuildingCreate,
  BuildingOut,
  BuildingUpdate,
  InvoiceOut,
  MeterOut,
  OrgOut,
  ReadingOut,
  TenantOut,
} from "./types";

// ── Organizacja ──
export const getOrg = () => apiFetch<OrgOut>("/organizations/me");

// ── Budynki ──
export const listBuildings = () => apiFetch<BuildingOut[]>("/buildings");
export const getBuilding = (id: string) => apiFetch<BuildingOut>(`/buildings/${id}`);
export const createBuilding = (body: BuildingCreate) =>
  apiFetch<BuildingOut>("/buildings", { method: "POST", body });
export const updateBuilding = (id: string, body: BuildingUpdate) =>
  apiFetch<BuildingOut>(`/buildings/${id}`, { method: "PATCH", body });

// ── Liczniki ──
export const listMeters = (buildingId?: string) =>
  apiFetch<MeterOut[]>("/meters", { params: { building_id: buildingId } });
export const listMeterReadings = (meterId: string) =>
  apiFetch<ReadingOut[]>(`/meters/${meterId}/readings`);

// ── Najemcy ──
export const listTenants = (buildingId?: string) =>
  apiFetch<TenantOut[]>("/tenants", { params: { building_id: buildingId } });

// ── Faktury ──
export const listInvoices = (params?: { tenant_id?: string; status?: string }) =>
  apiFetch<InvoiceOut[]>("/invoices", { params });
