// Convierte codigos del backend en frases legibles (Responsable: Aaron).
// El backend manda {code, params}; aqui se arma el texto en el idioma activo.

export function windowText(t, params, key = "act.window") {
  if (!params || params.from === undefined || params.to === undefined) return "";
  return t(key, { from: pad(params.from), to: pad(params.to) });
}

export function pad(h) {
  return String(h).padStart(2, "0");
}

export function actionText(t, action) {
  const p = action.params || {};
  return t(`act.${action.code}`, {
    ...p,
    hour: p.hour !== undefined && p.hour !== null ? pad(p.hour) : "",
    window: windowText(t, p),
  });
}

export function factorName(t, code) {
  return t(`factor.${code}`);
}

export function minutesAgo(t, minutes) {
  if (minutes === null || minutes === undefined) return t("data_never");
  if (minutes < 2) return t("data_updated_now");
  return t("data_updated", { min: minutes });
}

export function riskLine(t, risk) {
  const d = risk.detail || {};
  if (risk.type === "demand") {
    if (risk.direction === "low" && risk.score >= 15) return t("line.demand.low", { pct: Math.round(d.drop_pct || 0) });
    if (risk.direction === "high") return t("line.demand.high", { occ: Math.round((d.occupancy || 0) * 100) });
    return t("line.demand.normal");
  }
  if (risk.type === "delivery") {
    if (risk.window) return t("line.delivery.window", { from: pad(risk.window.from), to: pad(risk.window.to) });
    return t("line.delivery", { level: t(`level_${risk.level}`).toLowerCase() });
  }
  if (risk.type === "arrival") return t("line.arrival", { hour: pad((risk.hour + 1) % 24) });
  if (risk.type === "cost") {
    const fx = d.fx_change_30d_pct ?? 0;
    return t("line.cost", { fx_change: (fx > 0 ? "+" : "") + fx.toFixed(1), food: (d.food_inflation_12m_pct ?? 0).toFixed(1) });
  }
  return "";
}

export function headline(t, prediction) {
  const main = prediction.risks.find((r) => r.type === prediction.overall.main_risk);
  if (!main || main.score < 40) return { text: t("headline.calm"), cause: "" };
  const win = main.window ? t("headline.window", { from: pad(main.window.from), to: pad(main.window.to) }) : "";
  let key = `headline.${main.type}`;
  if (main.type === "demand") key = main.direction === "high" ? "headline.demand.high" : "headline.demand.low";
  const top = main.factors?.[0]?.factor;
  return { text: t(key, { window: win }), cause: top ? t("because", { factor: factorName(t, top) }) : "" };
}

export function formatTime(iso) {
  // "2026-11-02T20:00-05:00" -> "20:00"
  return iso ? iso.slice(11, 16) : "";
}

export function money(v) {
  return v === null || v === undefined ? "-" : Number(v).toFixed(2);
}
