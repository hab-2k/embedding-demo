import type { SearchResult } from "../api/client";

interface ResultCardProps {
  result: SearchResult;
  query: string;
}

function highlightText(text: string, query: string): JSX.Element[] {
  const terms = query
    .toLowerCase()
    .split(/\s+/)
    .filter((t) => t.length > 2);
  if (terms.length === 0) return [<span key="0">{text}</span>];

  const regex = new RegExp(`(${terms.map(escapeRegex).join("|")})`, "gi");
  const parts = text.split(regex);

  return parts.map((part, i) => {
    const isMatch = terms.some(
      (t) => part.toLowerCase() === t.toLowerCase()
    );
    return isMatch ? (
      <mark key={i} className="bg-lloyds-green-light text-lloyds-black px-0.5 rounded-sm font-medium">
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    );
  });
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function scoreColor(score: number): string {
  if (score >= 0.85) return "text-lloyds-green";
  if (score >= 0.7) return "text-lloyds-forest";
  return "text-lloyds-grey-dark";
}

export default function ResultCard({ result, query }: ResultCardProps) {
  const pct = (result.similarity_score * 100).toFixed(1);

  return (
    <div className="bg-white rounded-xl border border-lloyds-grey-mid/50 p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono bg-lloyds-green-50 text-lloyds-green px-2.5 py-1 rounded-md font-medium">
            {result.transcript_id}
          </span>
          <span className="text-xs text-lloyds-grey-dark">
            Chunks {result.start_index}–{result.end_index}
          </span>
        </div>
        <span className={`text-sm font-semibold ${scoreColor(result.similarity_score)}`}>
          {pct}%
        </span>
      </div>
      <p className="text-sm text-lloyds-black/85 leading-relaxed">
        {highlightText(result.text, query)}
      </p>
    </div>
  );
}
