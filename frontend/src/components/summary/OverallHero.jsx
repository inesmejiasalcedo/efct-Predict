// Tarjeta principal: como viene el dia en una frase (Responsable: Ines).
import { useI18n } from "../../i18n/LanguageContext";
import { headline } from "../../i18n/formatters";
import Gauge from "../ui/Gauge";
import { LevelBadge } from "../ui/Level";

export default function OverallHero({ prediction }) {
  const { t } = useI18n();
  const { overall } = prediction;
  const h = headline(t, prediction);
  return (
    <section className="card card-hero">
      <div className="row" style={{ gap: 24, alignItems: "center" }}>
        <div style={{ flex: "1 1 340px" }}>
          <div className="row" style={{ marginBottom: 10 }}>
            <LevelBadge level={overall.level} />
          </div>
          <h2 style={{ fontSize: 30, fontWeight: 800, marginBottom: 10 }}>{t(`overall_${overall.level}`)}</h2>
          <p style={{ fontSize: 18, fontWeight: 600 }}>{h.text}</p>
          {h.cause && <p className="muted" style={{ marginTop: 6 }}>{h.cause}</p>}
        </div>
        <div style={{ textAlign: "center", flex: "none" }}>
          <Gauge score={overall.score} level={overall.level} label={t("overall_score")} />
        </div>
      </div>
    </section>
  );
}
