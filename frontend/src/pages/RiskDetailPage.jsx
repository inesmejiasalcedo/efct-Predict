// Paginas de detalle por riesgo (Responsable: Diana).
// HU: Como gerente quiero entender por que un riesgo esta alto, cuando ocurre y que lo causa.
import { Link, NavLink, useParams } from "react-router-dom";
import { api } from "../api/client";
import FactorBreakdown from "../components/detail/FactorBreakdown";
import InputsPanel from "../components/detail/InputsPanel";
import ActionList from "../components/summary/ActionList";
import DataStatus from "../components/summary/DataStatus";
import Gauge from "../components/ui/Gauge";
import HourlyChart, { Legend } from "../components/ui/HourlyChart";
import { LEVEL_COLOR, LevelBadge } from "../components/ui/Level";
import RiskIcon from "../components/ui/RiskIcon";
import Spinner from "../components/ui/Spinner";
import { useI18n } from "../i18n/LanguageContext";
import { formatTime, riskLine } from "../i18n/formatters";
import useAsync from "../lib/useAsync";
import { useSite } from "../site/SiteContext";
import { NoSites } from "./SummaryPage";

const TYPES = ["demand", "delivery", "arrival", "cost"];

function levelColor(score) {
  return score >= 70 ? LEVEL_COLOR.high : score >= 40 ? LEVEL_COLOR.medium : LEVEL_COLOR.low;
}

function SeriesChart({ type, series, capacity }) {
  const { t } = useI18n();
  if (type === "cost") return null;
  if (type === "demand") {
    return (
      <>
        <HourlyChart
          data={series}
          bar={{ key: "expected_guests", label: t("chart_expected"), color: "#ffb14d" }}
          line={{ key: "normal_guests", label: t("chart_normal"), color: "#8a7f6c", dashed: true }}
          refLines={[{ value: capacity, label: t("chart_capacity"), color: "var(--high)" }]}
          yMax={Math.max(capacity * 1.1, 10)}
          closedLabel={t("chart_closed")}
          rainKey="rain_mm_h"
        />
        <Legend items={[{ label: t("chart_expected"), color: "#ffb14d" }, { label: t("chart_normal"), color: "#8a7f6c", line: true, dashed: true }, { label: t("chart_rain"), color: "rgba(58,110,165,0.5)" }]} />
      </>
    );
  }
  return (
    <HourlyChart
      data={series.map((s) => ({ ...s, in_service: type === "arrival" ? true : s.in_service }))}
      bar={{ key: type, label: t(`risk_short_${type}`), color: (d) => levelColor(d[type]) }}
      refLines={[
        { value: 40, label: t("detail_threshold_med"), color: "var(--medium)" },
        { value: 70, label: t("detail_threshold_high"), color: "var(--high)" },
      ]}
      yMax={100}
      closedLabel={t("chart_closed")}
      rainKey="rain_mm_h"
    />
  );
}

export default function RiskDetailPage() {
  const { type } = useParams();
  const { t, tError } = useI18n();
  const { siteId, loaded, sites } = useSite();
  const res = useAsync(
    () => (siteId && TYPES.includes(type) ? api(`/api/dashboard/risk/${type}`, { params: { site_id: siteId } }) : null),
    [siteId, type],
    { refreshMs: 5 * 60 * 1000 }
  );

  if (!loaded) return <Spinner />;
  if (!sites.length) return <NoSites />;
  if (!TYPES.includes(type)) return <div className="alert alert-error">404</div>;

  return (
    <div className="stack" style={{ gap: "var(--gap)" }}>
      <div>
        <Link to="/" className="faint" style={{ textDecoration: "none" }}>← {t("back")}</Link>
      </div>
      <nav className="tabs" style={{ marginBottom: 0 }}>
        {TYPES.map((tp) => (
          <NavLink key={tp} to={`/riesgo/${tp}`} className={({ isActive }) => `tab ${isActive ? "active" : ""}`}>
            {t(`risk_short_${tp}`)}
          </NavLink>
        ))}
      </nav>

      {res.loading && !res.data && <Spinner label={t("loading")} />}
      {res.error && <div className="alert alert-error">{tError(res.error)}</div>}
      {res.data && res.data.risk.type === type && <Detail data={res.data} />}
    </div>
  );
}

function Detail({ data }) {
  const { t } = useI18n();
  const { risk, series, inputs, site, data_status } = data;
  return (
    <>
      <section className="card card-hero">
        <div className="row" style={{ gap: 24 }}>
          <RiskIcon type={risk.type} size={28} />
          <div style={{ flex: "1 1 300px" }}>
            <div className="row" style={{ marginBottom: 6 }}>
              <h1 style={{ fontSize: 26, fontWeight: 800 }}>{t(`risk_${risk.type}`)}</h1>
              <LevelBadge level={risk.level} />
            </div>
            <p style={{ fontSize: 17, fontWeight: 600 }}>{riskLine(t, risk)}</p>
            {risk.time && <p className="muted" style={{ marginTop: 4 }}>{t("detail_peak", { time: formatTime(risk.time) })}</p>}
          </div>
          <Gauge score={risk.score} level={risk.level} size={170} />
        </div>
      </section>

      <div className="grid grid-3">
        <div className="card">
          <div className="card-title">{t("detail_why")}</div>
          <FactorBreakdown risk={risk} />
        </div>
        <div className="card span-2">
          <div className="card-title">{t("detail_actions")}</div>
          <ActionList actions={risk.actions} showRisk={false} />
        </div>
      </div>

      {risk.type !== "cost" && (
        <div className="card">
          <div className="card-title">{t("detail_series")}</div>
          <SeriesChart type={risk.type} series={series} capacity={site.capacity} />
        </div>
      )}

      <div className="grid grid-2">
        <div className="card">
          <div className="card-title">{t("detail_inputs")}</div>
          <InputsPanel type={risk.type} inputs={inputs} status={data_status} />
        </div>
        <div className="card stack" style={{ alignSelf: "start" }}>
          <div className="card-title">{t("detail_how")}</div>
          <p className="muted">{t(`how.${risk.type}`)}</p>
          <DataStatus status={data_status} />
        </div>
      </div>
    </>
  );
}
