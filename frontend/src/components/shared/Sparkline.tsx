// Sparkline — port 1:1 z mockupu (components.jsx).
export function Sparkline({
  data,
  w = 84,
  h = 26,
  color = "var(--accent)",
}: {
  data: number[];
  w?: number;
  h?: number;
  color?: string;
}) {
  if (!data || !data.length) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const pts = data.map((v, i): [number, number] => [
    (i / (data.length - 1)) * (w - 4) + 2,
    h - 3 - ((v - min) / span) * (h - 6),
  ]);
  const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  const last = pts[pts.length - 1];
  const up = data[data.length - 1] >= data[0];
  const stroke = color === "auto" ? (up ? "var(--accent)" : "var(--danger)") : color;
  return (
    <svg width={w} height={h} style={{ display: "block", overflow: "visible" }}>
      <path d={d} fill="none" stroke={stroke} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={last[0]} cy={last[1]} r="2.4" fill={stroke} />
    </svg>
  );
}

/** Sparkline + delta ▲/▼N% — port SparkCell z mockupu (screens.jsx). */
export function SparkCell({ data }: { data: number[] }) {
  if (!data || !data.length) return <span className="cell-sub">—</span>;
  const up = data[data.length - 1] >= data[0];
  const pct = Math.round(Math.abs((data[data.length - 1] - data[0]) / (data[0] || 1)) * 100);
  return (
    <div className="spark-cell">
      <Sparkline data={data} color="auto" />
      <span className={"spark-delta " + (up ? "up" : "down")}>
        {up ? "▲" : "▼"}
        {pct}%
      </span>
    </div>
  );
}
