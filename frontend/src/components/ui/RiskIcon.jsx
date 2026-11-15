// Iconos de cada riesgo (Responsable: Gabriel)
const PATHS = {
  demand: "M7 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm10 0a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM2 19c0-2.8 2.2-5 5-5s5 2.2 5 5M12 19c0-2.8 2.2-5 5-5s5 2.2 5 5",
  delivery: "M3 7h11v8H3zM14 10h4l3 3v2h-7M7 18a2 2 0 1 0 0-.01M18 18a2 2 0 1 0 0-.01",
  arrival: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",
  cost: "M12 3v18M16.5 7.5c-.8-1.2-2.5-2-4.5-2-2.5 0-4.5 1.3-4.5 3.2 0 4.3 9 2.3 9 6.5 0 1.9-2 3.3-4.5 3.3-2.2 0-4-.9-4.8-2.3",
};

export default function RiskIcon({ type, size = 22 }) {
  return (
    <span style={{ width: size + 16, height: size + 16, borderRadius: 12, background: "var(--brand-grad-soft)", display: "inline-grid", placeItems: "center", flex: "none" }}>
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="var(--brand-ink)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d={PATHS[type]} />
      </svg>
    </span>
  );
}
