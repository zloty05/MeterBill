import type { IconName } from "../shared/Icon";

export type ScreenId = "dashboard" | "budynki" | "liczniki" | "najemcy" | "taryfy" | "faktury";

export const NAV: { id: ScreenId; label: string; icon: IconName }[] = [
  { id: "dashboard", label: "Dashboard", icon: "grid" },
  { id: "budynki", label: "Budynki", icon: "building" },
  { id: "liczniki", label: "Liczniki", icon: "gauge" },
  { id: "najemcy", label: "Najemcy", icon: "users" },
  { id: "taryfy", label: "Taryfy", icon: "tag" },
  { id: "faktury", label: "Faktury", icon: "doc" },
];
