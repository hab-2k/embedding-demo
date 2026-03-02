import type { Theme } from "../api/client";
import Sparkline from "./Sparkline";

interface ThemeCardProps {
  theme: Theme;
  color: string;
  isExpanded: boolean;
  onToggle: () => void;
}

export default function ThemeCard({
  theme,
  color,
  isExpanded,
  onToggle,
}: ThemeCardProps) {
  const excerpts = isExpanded
    ? theme.representative_excerpts
    : theme.representative_excerpts.slice(0, 2);

  return (
    <div
      className="bg-white rounded-xl border border-lloyds-grey-mid/50 shadow-sm hover:shadow-md transition-shadow cursor-pointer flex overflow-hidden"
      onClick={onToggle}
    >
      <div className="w-1 shrink-0" style={{ backgroundColor: color }} />
      <div className="p-5 flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex flex-wrap gap-1.5">
            {theme.keywords.map((kw) => (
              <span
                key={kw}
                className="text-xs font-medium px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: color + "18",
                  color: color,
                }}
              >
                {kw}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {theme.timeline.length > 1 && (
              <Sparkline
                data={theme.timeline.map((tp) => tp.chunk_count)}
                color={color}
              />
            )}
            <span
              className="text-xs font-medium px-2.5 py-1 rounded-full"
              style={{
                backgroundColor: color + "15",
                color: color,
              }}
            >
              {theme.chunk_count} chunks
            </span>
          </div>
        </div>

        {theme.summary && (
          <p className="text-sm font-semibold text-lloyds-black mt-2">
            {theme.summary}
          </p>
        )}

        <div className="space-y-2.5 mt-2.5">
          {excerpts.map((excerpt) => (
            <div
              key={excerpt.chunk_id}
              className="text-xs text-lloyds-black/70 leading-relaxed border-l-2 pl-3"
              style={{ borderColor: color + "40" }}
            >
              <span className="font-mono text-lloyds-grey-dark text-[10px]">
                {excerpt.transcript_id}
              </span>
              <p className="mt-0.5 line-clamp-2">{excerpt.text}</p>
            </div>
          ))}
        </div>

        {theme.representative_excerpts.length > 2 && (
          <p className="text-[11px] text-lloyds-grey-dark mt-3">
            {isExpanded ? "Click to collapse" : `+${theme.representative_excerpts.length - 2} more excerpts`}
          </p>
        )}
      </div>
    </div>
  );
}
