import type { CSSProperties, ReactNode } from "react";

// Port 1:1 z mockupu (components.jsx) — własne kształty, te same co w prototypie.
// Trzymamy je zamiast Lucide, bo .nav-item .ico i styczne style liczą na klasę "ico".
export type IconName =
  | "grid"
  | "building"
  | "gauge"
  | "users"
  | "tag"
  | "doc"
  | "bolt"
  | "check"
  | "arrow"
  | "bell"
  | "plus"
  | "x"
  | "trash"
  | "logout";

const PATHS: Record<IconName, ReactNode> = {
  grid: (
    <g>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </g>
  ),
  building: (
    <g>
      <path d="M4 21V5l8-2v18" />
      <path d="M12 21V9l6 2v10" />
      <path d="M3 21h18" />
      <path d="M7 8h1M7 12h1M7 16h1" />
    </g>
  ),
  gauge: (
    <g>
      <circle cx="12" cy="13" r="8" />
      <path d="M12 13l4-3" />
      <path d="M12 5V3" />
    </g>
  ),
  users: (
    <g>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3.5 20c0-3.3 2.5-5.5 5.5-5.5s5.5 2.2 5.5 5.5" />
      <path d="M16 5.2a3 3 0 0 1 0 5.6M21 20c0-2.6-1.4-4.5-3.5-5.2" />
    </g>
  ),
  tag: (
    <g>
      <path d="M3 12V5a2 2 0 0 1 2-2h7l8 8-9 9z" />
      <circle cx="8" cy="8" r="1.4" />
    </g>
  ),
  doc: (
    <g>
      <path d="M6 3h8l5 5v13H6z" />
      <path d="M14 3v5h5" />
      <path d="M9 13h7M9 17h7" />
    </g>
  ),
  bolt: <path d="M13 2L4 14h7l-1 8 9-12h-7z" />,
  check: <path d="M4 12l5 5L20 6" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  bell: (
    <g>
      <path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6" />
      <path d="M10 20a2 2 0 0 0 4 0" />
    </g>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  x: <path d="M6 6l12 12M18 6L6 18" />,
  trash: (
    <g>
      <path d="M4 7h16" />
      <path d="M9 7V4h6v3" />
      <path d="M6.5 7l1 13h9l1-13" />
    </g>
  ),
  logout: (
    <g>
      <path d="M9 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </g>
  ),
};

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const style: CSSProperties = {
    width: size,
    height: size,
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };
  return (
    <svg viewBox="0 0 24 24" style={style} className="ico">
      {PATHS[name] ?? null}
    </svg>
  );
}
