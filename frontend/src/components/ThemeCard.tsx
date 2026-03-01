import type { Theme } from "../api/client";

interface ThemeCardProps {
  theme: Theme;
}

export default function ThemeCard({ theme }: ThemeCardProps) {
  return (
    <div className="bg-white rounded-xl border border-lloyds-grey-mid/50 p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-sm font-semibold text-lloyds-black leading-snug pr-4 line-clamp-2">
          {theme.label}
        </h3>
        <span className="shrink-0 text-xs font-medium bg-lloyds-green-50 text-lloyds-green px-2.5 py-1 rounded-full">
          {theme.chunk_count} chunks
        </span>
      </div>
      <div className="space-y-3">
        {theme.representative_excerpts.slice(0, 3).map((excerpt) => (
          <div
            key={excerpt.chunk_id}
            className="text-xs text-lloyds-black/70 leading-relaxed border-l-2 border-lloyds-green/30 pl-3"
          >
            <span className="font-mono text-lloyds-grey-dark text-[10px]">
              {excerpt.transcript_id}
            </span>
            <p className="mt-0.5 line-clamp-2">{excerpt.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
