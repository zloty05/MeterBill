/** @type {import('tailwindcss').Config} */
// Tokeny z frontend/docs/design_files/styles.css (źródło prawdy designu).
// Tailwind używamy głównie do utility/layoutu; szczegółowy look żyje w src/styles/*.css
// (klasy .btn/.pill/.card.sketch/.table.wf itd. portowane 1:1), więc trzymamy pixel-perfect.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1d2826",
        "ink-soft": "#5a6a65",
        "ink-faint": "#93a09b",
        paper: "#ffffff",
        line: "#e6eae8",
        "line-strong": "#d6dcda",
        fill: "#f1f5f3",
        "fill-2": "#e8edeb",
        "fill-3": "#f8faf9",
        accent: "oklch(0.65 0.14 160)",
        "accent-deep": "oklch(0.5 0.13 162)",
        "accent-soft": "oklch(0.965 0.028 165)",
        "accent-line": "oklch(0.86 0.06 165)",
        warn: "oklch(0.72 0.13 70)",
        "warn-ink": "oklch(0.46 0.10 68)",
        danger: "oklch(0.6 0.16 25)",
        "danger-soft": "oklch(0.965 0.03 28)",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "-apple-system", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", '"SF Mono"', "Menlo", "monospace"],
      },
      borderRadius: {
        DEFAULT: "12px",
        sm: "9px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(20,40,35,0.05), 0 2px 8px rgba(20,40,35,0.05)",
      },
    },
  },
  plugins: [],
};
