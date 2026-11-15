// Datos externos que alimentan el calculo, con su fuente (Responsable: Diana).
import { useI18n } from "../../i18n/LanguageContext";
import { minutesAgo } from "../../i18n/formatters";
import { SimBadge } from "../ui/Level";

function Row({ label, value }) {
  return (
    <div className="row" style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
      <span className="muted">{label}</span>
      <span className="spacer" />
      <span className="strong">{value}</span>
    </div>
  );
}

function Spark({ series }) {
  if (!series?.length) return null;
  const vals = series.map((p) => p.value);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const pts = vals.map((v, i) => `${(i / Math.max(vals.length - 1, 1)) * 200},${40 - ((v - min) / (max - min || 1)) * 36}`).join(" ");
  return (
    <svg viewBox="0 0 200 44" width="100%" height="44" style={{ marginTop: 8 }}>
      <polyline points={pts} fill="none" stroke="var(--brand-4)" strokeWidth="2" />
    </svg>
  );
}

export default function InputsPanel({ type, inputs, status }) {
  const { t } = useI18n();
  const src = (name) => status?.sources?.find((s) => s.source === name);
  const w = inputs.weather;
  const tr = inputs.traffic;
  const m = inputs.macro;
  const blocks = [];

  if (type !== "cost") {
    blocks.push(
      <div key="w">
        <div className="row"><b>OpenWeather</b><span className="faint">{minutesAgo(t, src("weather")?.age_minutes)}</span>{src("weather")?.is_simulated && <SimBadge />}</div>
        <Row label={t("input_temp")} value={w ? `${w.temp_c}°C` : "-"} />
        <Row label={t("input_rain")} value={w ? `${w.rain_mm_h} mm/h` : "-"} />
        <Row label={t("input_humidity")} value={w ? `${w.humidity}%` : "-"} />
      </div>
    );
    blocks.push(
      <div key="t">
        <div className="row"><b>TomTom</b><span className="faint">{minutesAgo(t, src("traffic")?.age_minutes)}</span>{src("traffic")?.is_simulated && <SimBadge />}</div>
        <Row label={t("input_congestion")} value={tr ? `${Math.round(tr.congestion * 100)}%` : "-"} />
        <Row label={t("input_speed")} value={tr ? `${tr.current_speed_kmh} / ${tr.free_flow_speed_kmh} km/h` : "-"} />
      </div>
    );
  }
  blocks.push(
    <div key="m">
      <div className="row"><b>BCRP</b><span className="faint">{minutesAgo(t, src("macro")?.age_minutes)}</span>{src("macro")?.is_simulated && <SimBadge />}</div>
      <Row label={t("input_fx")} value={m?.fx_last ? `S/ ${m.fx_last.toFixed(3)}` : "-"} />
      <Row label={t("input_fx_change")} value={m ? `${(m.fx_change_30d_pct ?? 0).toFixed(2)}%` : "-"} />
      <Row label={t("input_food")} value={m?.food_inflation_12m_pct != null ? `${m.food_inflation_12m_pct.toFixed(2)}%` : "-"} />
      {type === "cost" && <Spark series={m?.fx_series} />}
    </div>
  );
  return <div className="stack" style={{ gap: 18 }}>{blocks}</div>;
}
