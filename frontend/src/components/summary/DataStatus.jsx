// Frescura de los datos + boton para actualizar (Responsable: Ines; tambien lo usa Diana).
import { useI18n } from "../../i18n/LanguageContext";
import { minutesAgo } from "../../i18n/formatters";
import { SimBadge } from "../ui/Level";

export default function DataStatus({ status, onRefresh, refreshing, showNotice = true }) {
  const { t } = useI18n();
  if (!status) return null;
  const sources = status.sources || [];
  const freshest = Math.min(...sources.filter((s) => s.age_minutes !== null).map((s) => s.age_minutes), Infinity);
  const sim = status.simulated_sources || [];
  const missing = Object.entries(status.keys || {}).filter(([, ok]) => !ok).map(([k]) => (k === "openweather" ? "OpenWeather" : "TomTom"));
  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="row">
        <span className="faint">{minutesAgo(t, Number.isFinite(freshest) ? freshest : null)} · {t("data_auto")}</span>
        {sim.length > 0 && <SimBadge />}
        <span className="spacer" />
        {onRefresh && (
          <button className="btn btn-sm" onClick={onRefresh} disabled={refreshing}>
            {refreshing ? t("refreshing") : t("refresh")}
          </button>
        )}
      </div>
      {showNotice && sim.length > 0 && (
        <div className="alert alert-warn" style={{ fontSize: 13 }}>
          {missing.length > 0
            ? t("data_simulated_help", { missing: missing.join(", ") })
            : t("data_partial_sim", { sources: sim.map((s) => t(`source.${s}`)).join(", ") })}
        </div>
      )}
    </div>
  );
}

// Aviso cuando hay fuentes simuladas (faltan API keys)
export function SimulatedNotice({ status }) {
  const { t } = useI18n();
  const sim = status?.simulated_sources || [];
  if (!sim.length) return null;
  const missing = Object.entries(status.keys || {}).filter(([, ok]) => !ok).map(([k]) => (k === "openweather" ? "OpenWeather" : "TomTom"));
  return (
    <div className="alert alert-warn" style={{ fontSize: 13 }}>
      {missing.length > 0
        ? t("data_simulated_help", { missing: missing.join(", ") })
        : t("data_partial_sim", { sources: sim.map((s) => t(`source.${s}`)).join(", ") })}
    </div>
  );
}
