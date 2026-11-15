// Etiquetas, barras y colores por nivel de riesgo (Responsable: Gabriel)
import { useI18n } from "../../i18n/LanguageContext";

export const LEVEL_COLOR = { low: "var(--low)", medium: "var(--medium)", high: "var(--high)" };

export function LevelBadge({ level }) {
  const { t } = useI18n();
  return (
    <span className={`badge badge-${level}`}>
      <span className="dot" />
      {t(`level_${level}`)}
    </span>
  );
}

export function ScoreBar({ score, level }) {
  return (
    <div className="bar" aria-label={`${score}/100`}>
      <span style={{ width: `${Math.max(score, 3)}%`, background: LEVEL_COLOR[level] }} />
    </div>
  );
}

export function SimBadge() {
  const { t } = useI18n();
  return <span className="badge badge-sim">{t("data_simulated")}</span>;
}
