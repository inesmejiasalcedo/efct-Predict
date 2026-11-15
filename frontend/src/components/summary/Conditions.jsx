// Condiciones externas actuales en lenguaje simple (Responsable: Ines).
import { useI18n } from "../../i18n/LanguageContext";

function Item({ label, value, sub }) {
  return (
    <div style={{ padding: "4px 0" }}>
      <div className="faint">{label}</div>
      <div className="strong" style={{ fontSize: 20 }}>{value}</div>
      {sub && <div className="muted" style={{ fontSize: 13 }}>{sub}</div>}
    </div>
  );
}

export default function Conditions({ current }) {
  const { t } = useI18n();
  const w = current?.weather;
  const tr = current?.traffic;
  const m = current?.macro;
  return (
    <div className="card">
      <div className="card-title">{t("now_conditions")}</div>
      <div className="grid grid-3" style={{ gap: 12 }}>
        <Item
          label={t("weather_now")}
          value={w ? `${Math.round(w.temp_c)}°C` : "-"}
          sub={w ? (w.rain_mm_h > 0 ? t("rain_mm", { mm: w.rain_mm_h }) : t("no_rain")) : ""}
        />
        <Item
          label={t("traffic_now")}
          value={tr ? t("congestion_pct", { pct: Math.round(tr.congestion * 100) }) : "-"}
          sub={tr ? `${tr.current_speed_kmh} / ${tr.free_flow_speed_kmh} km/h` : ""}
        />
        <Item
          label={t("fx_now")}
          value={m?.fx_last ? `S/ ${m.fx_last.toFixed(3)}` : "-"}
          sub={m ? `${m.fx_change_30d_pct > 0 ? "+" : ""}${(m.fx_change_30d_pct ?? 0).toFixed(1)}% (30d)` : ""}
        />
      </div>
    </div>
  );
}
