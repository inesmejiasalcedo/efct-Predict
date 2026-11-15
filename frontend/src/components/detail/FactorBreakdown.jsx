// Que factores empujan el riesgo y cuanto pesa cada uno (Responsable: Diana).
import { useI18n } from "../../i18n/LanguageContext";
import { factorName } from "../../i18n/formatters";

const capitalize = (s) => s.charAt(0).toUpperCase() + s.slice(1);

export default function FactorBreakdown({ risk }) {
  const { t } = useI18n();
  const factors = (risk.factors || []).filter((f) => (f.share_pct ?? 0) > 0);
  if (!factors.length) return <p className="muted">-</p>;
  const isDemand = risk.type === "demand";
  return (
    <div className="stack" style={{ gap: 14 }}>
      {factors.map((f) => (
        <div key={f.factor}>
          <div className="row" style={{ marginBottom: 6 }}>
            <span style={{ fontWeight: 600 }}>{capitalize(factorName(t, f.factor))}</span>
            <span className="spacer" />
            <span className="faint">
              {isDemand && f.impact < 0 ? `${t("lowers")} ${Math.round(-f.impact * 100)}% · ` : ""}
              {t("impact_share", { pct: f.share_pct })}
            </span>
          </div>
          <div className="bar" style={{ height: 10 }}>
            <span style={{ width: `${f.share_pct}%`, background: "var(--brand-grad)" }} />
          </div>
        </div>
      ))}
    </div>
  );
}
