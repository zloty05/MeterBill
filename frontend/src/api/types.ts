// Typy kontraktu API — lustro schematów *Out z backendu (api/schemas/*.py).
// To kontrakt sieci, NIE kształt z mockupowego data.js (mockup ma agregaty
// online/toSend/overdue/kWh, których backend listowy nie zwraca).

export type UUID = string;
export type ISODateTime = string; // np. "2026-06-04T09:12:00Z"
export type ISODate = string; // np. "2026-06-04"

export type OrgPlan = "free" | "pro" | "enterprise";

export interface OrgOut {
  id: UUID;
  name: string;
  nip: string | null;
  address: string | null;
  bank_account: string | null;
  plan: OrgPlan;
  created_at: ISODateTime | null;
}

export interface BuildingOut {
  id: UUID;
  org_id: UUID;
  name: string;
  address: string;
  main_meter_ppe: string | null;
  created_at: ISODateTime | null;
}

export interface BuildingCreate {
  name: string;
  address: string;
  main_meter_ppe?: string | null;
}

export interface BuildingUpdate {
  name?: string | null;
  address?: string | null;
  main_meter_ppe?: string | null;
}

export type MeterProtocol = "mbus" | "modbus" | "opcua" | "manual";

export interface MeterOut {
  id: UUID;
  building_id: UUID;
  tariff_id: UUID | null;
  serial_no: string;
  mbus_address: string | null;
  protocol: MeterProtocol;
  ppe_code: string | null;
  tariff_group: string;
  label: string | null;
  created_at: ISODateTime | null;
}

export interface MeterCreate {
  building_id: UUID;
  serial_no: string;
  tariff_id?: UUID | null;
  mbus_address?: string | null;
  protocol?: MeterProtocol;
  ppe_code?: string | null;
  tariff_group?: string;
  label?: string | null;
}

export interface MeterUpdate {
  serial_no?: string | null;
  tariff_id?: UUID | null;
  mbus_address?: string | null;
  protocol?: MeterProtocol | null;
  ppe_code?: string | null;
  tariff_group?: string | null;
  label?: string | null;
}

export interface TenantOut {
  id: UUID;
  building_id: UUID;
  name: string;
  email: string;
  unit_no: string;
  nip: string | null;
  active: boolean;
  created_at: ISODateTime | null;
}

export interface TenantCreate {
  building_id: UUID;
  name: string;
  email: string;
  unit_no: string;
  nip?: string | null;
  active?: boolean;
}

export interface TenantUpdate {
  name?: string | null;
  email?: string | null;
  unit_no?: string | null;
  nip?: string | null;
  active?: boolean | null;
}

export interface ReadingOut {
  id: UUID;
  meter_id: UUID;
  read_at: ISODateTime;
  read_type: string;
  value_kwh: string; // Decimal serializowany jako string
  power_kw: string | null;
  is_estimated: boolean;
  source: string | null;
  created_at: ISODateTime | null;
}

export type InvoiceStatus = "draft" | "ready" | "sent" | "paid" | "overdue";

export interface InvoiceLineOut {
  label: string;
  quantity: string;
  unit: string;
  unit_price: string;
  net_amount: string;
  vat_rate: string;
  component_id: UUID | null;
  sort_order: number | null;
}

export interface InvoiceOut {
  id: UUID;
  tenant_id: UUID;
  invoice_no: string | null;
  period_from: ISODate;
  period_to: ISODate;
  kwh_consumed: string;
  net_amount: string;
  vat_amount: string;
  gross_amount: string;
  status: InvoiceStatus;
  due_date: ISODate | null;
  is_estimated: boolean;
  issued_date: ISODate | null;
  sent_at: ISODateTime | null;
  paid_at: ISODateTime | null;
  pdf_path: string | null;
  created_at: ISODateTime | null;
  lines?: InvoiceLineOut[];
}
