// Pagina de Resumen (Responsable: Ines).
// HU: Como gerente quiero ver en una sola pantalla como viene el dia y que hacer al respecto.
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import ActionList from "../components/summary/ActionList";
import Conditions from "../components/summary/Conditions";
import DataStatus, { SimulatedNotice } from "../components/summary/DataStatus";
import OverallHero from "../components/summary/OverallHero";
import RiskCard from "../components/summary/RiskCard";
import HourlyChart, { Legend } from "../components/ui/HourlyChart";
import Spinner from "../components/ui/Spinner";
import { useI18n } from "../i18n/LanguageContext";
import useAsync from "../lib/useAsync";
import { useSite } from "../site/SiteContext";

const REFRESH_MS = 5 * 60 * 1000; // la pantalla se refresca sola cada 5 min

export function NoSites() {
  const { t } = useI18n();
  return (
    <div className="card empty">
      <h3>{t("no_sites_title")}</h3>
      <p>{t("no_sites_text")}</p>
      <Link to="/negocio" className="btn btn-primary">{t("no_sites_btn")}</Link>
    </div>
  );
}

function guestColor(d) {
  if (!d.in_service) return "transparent";
  if (d.expected_guests >= d.normal_guests * 1.15) return "var(--high)"; // mas gente de lo normal
  if (d.expected_guests < d.normal_guests * 0.8) return "#f6cf8a"; // bastante menos de lo normal
  return "#ffb14d";
}

export default function SummaryPage() {
  const { t, tError } = useI18n();
  const { site, siteId, loaded, sites } = useSite();
  const [refreshing, setRefreshing] = useState(false);
  const pred = useAsync(() => (siteId ? api("/api/dashboard/summary", { params: { site_id: siteId } }) : null), [siteId], { refreshMs: REFRESH_MS });
  const model = useAsync(() => api("/api/dashboard/model"), []);

  if (!loaded) return <Spinner />;
  if (!sites.length) return <NoSites />;
  if (pred.loading && !pred.data) return <Spinner label={t("loading")} />;
  if (pred.error) return <div className="alert alert-error">{tError(pred.error)}</div>;
  const p = pred.data;
  if (!p) return null;

  async function refresh() {
    setRefreshing(true);
    try {
      await api("/api/data/refresh", { method: "POST", params: { site_id: siteId } });
      await pred.reload(true);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="stack" style={{ gap: "var(--gap)" }}>
      <div className="page-head" style={{ marginBottom: 0 }}>
        <div>
          <h1 className="page-title">{t("summary_title")}</h1>
          <p className="page-sub">{t("summary_sub", { site: site?.name })}</p>
        </div>
        <div style={{ minWidth: 280, flex: "0 1 520px" }}>
          <DataStatus status={p.data_status} onRefresh={refresh} refreshing={refreshing} showNotice={false} />
        </div>
      </div>

      <SimulatedNotice status={p.data_status} />

      <OverallHero prediction={p} />

      <div className="grid grid-4">
        {p.risks.map((r) => (
          <RiskCard key={r.type} risk={r} />
        ))}
      </div>

      <div className="grid grid-3">
        <div className="card span-2">
          <div className="card-title">
            {t("chart_guests_title")}
            <span className="hint">{t("chart_capacity")}: {p.site.capacity} {t("people")}</span>
          </div>
          <HourlyChart
            data={p.hourly}
            bar={{ key: "expected_guests", label: t("chart_expected"), color: guestColor }}
            line={{ key: "normal_guests", label: t("chart_normal"), color: "#8a7f6c", dashed: true }}
            refLines={[{ value: p.site.capacity, label: t("chart_capacity"), color: "var(--high)" }]}
            yMax={Math.max(p.site.capacity * 1.1, 10)}
            closedLabel={t("chart_closed")}
            rainKey="rain_mm_h"
          />
          <Legend
            items={[
              { label: t("chart_expected"), color: "#ffb14d" },
              { label: t("chart_normal"), color: "#8a7f6c", line: true, dashed: true },
              { label: t("chart_rain"), color: "rgba(58,110,165,0.5)" },
              { label: t("chart_closed"), color: "#f1ece2" },
            ]}
          />
        </div>
        <div className="card">
          <div className="card-title">{t("what_to_do")}</div>
          <ActionList actions={p.top_actions} />
        </div>
      </div>

      <Conditions current={p.current} />

      {model.data && (
        <p className="faint" style={{ textAlign: "center" }}>
          {t("model_quality", { acc: Math.round(model.data.delivery.accuracy * 100), mae: Math.round(model.data.demand.mae * 100) })}
        </p>
      )}
    </div>
  );
}
