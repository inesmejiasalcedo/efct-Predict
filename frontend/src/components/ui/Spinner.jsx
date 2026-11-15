// Indicador de carga (Responsable: Gabriel)
export default function Spinner({ full = false, label }) {
  return (
    <div className="center" style={full ? { minHeight: "100vh" } : undefined}>
      <div className="spinner" />
      {label && <span className="faint">{label}</span>}
    </div>
  );
}
