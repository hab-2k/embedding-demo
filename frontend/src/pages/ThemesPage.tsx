import { useEffect, useState } from "react";
import ThemeCard from "../components/ThemeCard";
import { getThemes } from "../api/client";
import type { Theme } from "../api/client";

export default function ThemesPage() {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    getThemes()
      .then((res) => setThemes(res.themes))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load themes")
      )
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-lloyds-black tracking-tight">
          Themes
        </h1>
        <p className="text-sm text-lloyds-grey-dark mt-1">
          Auto-discovered topic clusters across all transcripts
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <svg className="animate-spin h-8 w-8 text-lloyds-green" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!isLoading && !error && themes.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {themes.map((theme) => (
            <ThemeCard key={theme.cluster_id} theme={theme} />
          ))}
        </div>
      )}

      {!isLoading && !error && themes.length === 0 && (
        <div className="text-center py-20">
          <p className="text-sm text-lloyds-grey-dark">
            No themes available. Ingest some transcripts first.
          </p>
        </div>
      )}
    </div>
  );
}
