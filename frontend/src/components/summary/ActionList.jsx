// Lista de acciones recomendadas (Responsable: Ines; tambien la usa Diana).
import { useI18n } from "../../i18n/LanguageContext";
import { actionText } from "../../i18n/formatters";

const PRIORITY_COLOR = { 1: "var(--high)", 2: "var(--medium)", 3: "var(--low)" };

export default function ActionList({ actions, showRisk = true }) {
  const { t } = useI18n();
  if (!actions?.length) return <p className="muted">{t("nothing_to_do")}</p>;
  return (
    <ol className="stack" style={{ listStyle: "none", padding: 0, margin: 0, gap: 10 }}>
      {actions.map((a, i) => (
        <li key={i} className="row" style={{ alignItems: "flex-start", gap: 12, padding: "10px 12px", borderRadius: 12, background: "var(--bg-soft)" }}>
          <span style={{ width: 24, height: 24, borderRadius: "50%", background: PRIORITY_COLOR[a.priority], color: "#fff", display: "grid", placeItems: "center", fontSize: 12, fontWeight: 800, flex: "none" }}>
            {i + 1}
          </span>
          <div>
            <div style={{ fontWeight: 600 }}>{actionText(t, a)}</div>
            {showRisk && <div className="faint">{t(`risk_${a.risk}`)}</div>}
          </div>
        </li>
      ))}
    </ol>
  );
}
