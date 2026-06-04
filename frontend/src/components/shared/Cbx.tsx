// Checkbox — port z mockupu. Styl w tokens.css (.cbx / .cbx.on).
export function Cbx({ on, onClick }: { on: boolean; onClick?: () => void }) {
  return (
    <div
      className={"cbx" + (on ? " on" : "")}
      onClick={onClick}
      role="checkbox"
      aria-checked={on}
    >
      <svg
        viewBox="0 0 24 24"
        width="13"
        height="13"
        style={{
          fill: "none",
          stroke: "#fff",
          strokeWidth: 3,
          strokeLinecap: "round",
          strokeLinejoin: "round",
        }}
      >
        <path d="M4 12l5 5L20 6" />
      </svg>
    </div>
  );
}
