import type { RiskFlag } from "../api/client";

interface RiskFlagCardProps {
  flag: RiskFlag;
}

function severityStyle(score: number): { border: string; badge: string; badgeText: string } {
  if (score >= 0.85) {
    return {
      border: "border-l-red-500",
      badge: "bg-red-50 text-red-700",
      badgeText: "High",
    };
  }
  return {
    border: "border-l-amber-500",
    badge: "bg-amber-50 text-amber-700",
    badgeText: "Medium",
  };
}

export default function RiskFlagCard({ flag }: RiskFlagCardProps) {
  const pct = (flag.similarity_score * 100).toFixed(1);
  const severity = severityStyle(flag.similarity_score);

  return (
    <div className={`bg-white rounded-xl border border-lloyds-grey-mid/50 border-l-4 ${severity.border} p-5 shadow-sm hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono bg-lloyds-green-50 text-lloyds-green px-2.5 py-1 rounded-md font-medium">
            {flag.transcript_id}
          </span>
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${severity.badge}`}>
            {severity.badgeText}
          </span>
        </div>
        <span className="text-sm font-semibold text-lloyds-black">{pct}%</span>
      </div>
      <p className="text-sm text-lloyds-black/85 leading-relaxed mb-3">
        {flag.text}
      </p>
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider text-lloyds-grey-dark font-medium">
          Triggered by
        </span>
        <span className="text-xs bg-lloyds-seashell text-lloyds-black px-2.5 py-1 rounded-md font-medium italic">
          "{flag.seed_phrase}"
        </span>
      </div>
    </div>
  );
}
