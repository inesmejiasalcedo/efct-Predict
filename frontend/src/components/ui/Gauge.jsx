// Medidor semicircular 0-100 (Responsable: Gabriel)
import { LEVEL_COLOR } from "./Level";

export default function Gauge({ score, level, size = 180, label }) {
  const r = 70;
  const circumference = Math.PI * r;
  const filled = (Math.min(Math.max(score, 0), 100) / 100) * circumference;
  return (
    <svg width={size} height={size * 0.62} viewBox="0 0 180 112" role="img" aria-label={`${score}/100`}>
      <path d="M20 95 A70 70 0 0 1 160 95" fill="none" stroke="#f0eadf" strokeWidth="16" strokeLinecap="round" />
      <path
        d="M20 95 A70 70 0 0 1 160 95"
        fill="none"
        stroke={LEVEL_COLOR[level]}
        strokeWidth="16"
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circumference}`}
        style={{ transition: "stroke-dasharray 0.6s ease" }}
      />
      <text x="90" y="86" textAnchor="middle" fontSize="34" fontWeight="800" fill="var(--text)">
        {score}
      </text>
      {label && (
        <text x="90" y="106" textAnchor="middle" fontSize="11" fill="var(--muted)">
          {label}
        </text>
      )}
    </svg>
  );
}
