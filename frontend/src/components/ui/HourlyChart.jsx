// Grafico por hora en SVG puro, sin librerias (Responsable: Gabriel).
// bars: barras principales | line: linea de referencia | refLines: lineas horizontales fijas
import { useState } from "react";
import { pad } from "../../i18n/formatters";

const W = 760;
const H = 250;
const M = { top: 16, right: 12, bottom: 30, left: 38 };

export default function HourlyChart({ data, bar, line, refLines = [], yMax, closedLabel, rainKey, unit = "" }) {
  const [hover, setHover] = useState(null);
  if (!data?.length) return null;
  const innerW = W - M.left - M.right;
  const innerH = H - M.top - M.bottom;
  const maxVal = yMax ?? Math.max(1, ...data.map((d) => Math.max(d[bar.key] || 0, line ? d[line.key] || 0 : 0)), ...refLines.map((r) => r.value)) * 1.1;
  const step = innerW / data.length;
  const x = (i) => M.left + i * step;
  const y = (v) => M.top + innerH - (Math.min(v, maxVal) / maxVal) * innerH;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(maxVal * f));
  const maxRain = Math.max(0.5, ...(rainKey ? data.map((d) => d[rainKey] || 0) : [0]));

  const linePath = line
    ? data.map((d, i) => `${i === 0 ? "M" : "L"}${x(i) + step / 2},${y(d[line.key] || 0)}`).join(" ")
    : null;

  return (
    <div style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" onMouseLeave={() => setHover(null)}>
        {ticks.map((tk) => (
          <g key={tk}>
            <line x1={M.left} x2={W - M.right} y1={y(tk)} y2={y(tk)} stroke="#f1ece2" />
            <text x={M.left - 6} y={y(tk) + 4} textAnchor="end" fontSize="10" fill="var(--faint)">{tk}</text>
          </g>
        ))}

        {data.map((d, i) =>
          d.in_service === false ? (
            <rect key={`c${i}`} x={x(i)} y={M.top} width={step} height={innerH} fill="#faf7f1" />
          ) : null
        )}

        {rainKey &&
          data.map((d, i) =>
            d[rainKey] >= 0.1 ? (
              <rect key={`r${i}`} x={x(i) + step * 0.15} y={M.top} width={step * 0.7} height={(d[rainKey] / maxRain) * 26} fill="rgba(58,110,165,0.35)" rx="2" />
            ) : null
          )}

        {data.map((d, i) => {
          const v = d[bar.key] || 0;
          const color = typeof bar.color === "function" ? bar.color(d) : bar.color;
          return (
            <rect
              key={`b${i}`}
              x={x(i) + step * 0.18}
              y={y(v)}
              width={step * 0.64}
              height={Math.max(innerH + M.top - y(v), v > 0 ? 2 : 0)}
              rx="4"
              fill={color}
              opacity={hover === null || hover === i ? 1 : 0.55}
            />
          );
        })}

        {refLines.map((r) => (
          <g key={r.label}>
            <line x1={M.left} x2={W - M.right} y1={y(r.value)} y2={y(r.value)} stroke={r.color} strokeDasharray="5 4" strokeWidth="1.5" />
            <text x={M.left + 6} y={y(r.value) - 5} fontSize="10" fontWeight="600" fill={r.color} stroke="#fff" strokeWidth="3" paintOrder="stroke">{r.label}</text>
          </g>
        ))}

        {linePath && <path d={linePath} fill="none" stroke={line.color} strokeWidth="2" strokeDasharray={line.dashed ? "4 4" : undefined} />}

        {data.map((d, i) =>
          i % 2 === 0 ? (
            <text key={`x${i}`} x={x(i) + step / 2} y={H - 10} textAnchor="middle" fontSize="10" fill="var(--muted)">
              {pad(d.hour)}h
            </text>
          ) : null
        )}

        {data.map((d, i) => (
          <rect key={`h${i}`} x={x(i)} y={M.top} width={step} height={innerH} fill="transparent" onMouseEnter={() => setHover(i)} onClick={() => setHover(i)} />
        ))}
      </svg>

      {hover !== null && (
        <div
          style={{
            position: "absolute", top: 4, left: `${Math.min(((x(hover) + step) / W) * 100, 72)}%`,
            background: "#fff", border: "1px solid var(--border)", borderRadius: 10, padding: "8px 10px",
            fontSize: 12, boxShadow: "var(--shadow)", pointerEvents: "none", minWidth: 130,
          }}
        >
          <div className="strong">{pad(data[hover].hour)}:00</div>
          {data[hover].in_service === false ? (
            <div className="muted">{closedLabel}</div>
          ) : (
            <>
              <div>{bar.label}: <b>{data[hover][bar.key]}{unit}</b></div>
              {line && <div>{line.label}: <b>{data[hover][line.key]}{unit}</b></div>}
            </>
          )}
          {rainKey && data[hover][rainKey] >= 0.1 && <div style={{ color: "var(--info)" }}>{data[hover][rainKey]} mm/h</div>}
        </div>
      )}
    </div>
  );
}

export function Legend({ items }) {
  return (
    <div className="row" style={{ gap: 14, fontSize: 12, color: "var(--muted)" }}>
      {items.map((it) => (
        <span key={it.label} className="row" style={{ gap: 6 }}>
          <span style={{ width: 12, height: it.line ? 2 : 10, borderRadius: 3, background: it.color, borderTop: it.dashed ? `2px dashed ${it.color}` : undefined }} />
          {it.label}
        </span>
      ))}
    </div>
  );
}
