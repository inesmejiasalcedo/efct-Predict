// Tarjeta resumen de un riesgo, enlaza a su pagina de detalle (Responsable: Ines).
import { Link } from "react-router-dom";
import { useI18n } from "../../i18n/LanguageContext";
import { riskLine } from "../../i18n/formatters";
import { LevelBadge, ScoreBar } from "../ui/Level";
import RiskIcon from "../ui/RiskIcon";

export default function RiskCard({ risk }) {
  const { t } = useI18n();
  return (
    <Link to={`/riesgo/${risk.type}`} className="card link stack" style={{ gap: 14 }}>
      <div className="row" style={{ alignItems: "flex-start" }}>
        <RiskIcon type={risk.type} />
        <span className="spacer" />
        <LevelBadge level={risk.level} />
      </div>
      <div>
        <div className="strong" style={{ fontSize: 16 }}>{t(`risk_${risk.type}`)}</div>
        <div className="muted" style={{ fontSize: 14, minHeight: 42, marginTop: 4 }}>{riskLine(t, risk)}</div>
      </div>
      <div className="row" style={{ gap: 10 }}>
        <div style={{ flex: 1 }}>
          <ScoreBar score={risk.score} level={risk.level} />
        </div>
        <span className="strong">{risk.score}</span>
      </div>
      <span className="faint">{t("see_detail")} →</span>
    </Link>
  );
}
