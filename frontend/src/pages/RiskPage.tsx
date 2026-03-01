import { useEffect, useState } from "react";
import RiskFlagCard from "../components/RiskFlagCard";
import { getRiskFlags } from "../api/client";
import type { RiskFlag } from "../api/client";

export default function RiskPage() {
  const [flags, setFlags] = useState<RiskFlag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    getRiskFlags()
      .then((res) => setFlags(res.flags))
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Failed to load risk flags"
        )
      )
      .finally(() => setIsLoading(false));
  }, []);

  const highCount = flags.filter((f) => f.similarity_score >= 0.85).length;
  const mediumCount = flags.filter(
    (f) => f.similarity_score >= 0.75 && f.similarity_score < 0.85
  ).length;

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-lloyds-black tracking-tight">
          Risk Flags
        </h1>
        <p className="text-sm text-lloyds-grey-dark mt-1">
          Transcript chunks matching vulnerability and complaint indicators
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

      {!isLoading && !error && flags.length > 0 && (
        <>
          <div className="flex items-center gap-4 mb-6">
            <div className="flex items-center gap-1.5 bg-red-50 px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-xs font-medium text-red-700">
                {highCount} High
              </span>
            </div>
            <div className="flex items-center gap-1.5 bg-amber-50 px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-xs font-medium text-amber-700">
                {mediumCount} Medium
              </span>
            </div>
          </div>
          <div className="space-y-3">
            {flags.map((flag) => (
              <RiskFlagCard key={flag.chunk_id} flag={flag} />
            ))}
          </div>
        </>
      )}

      {!isLoading && !error && flags.length === 0 && (
        <div className="text-center py-20">
          <p className="text-sm text-lloyds-grey-dark">
            No risk flags detected. Ingest some transcripts first.
          </p>
        </div>
      )}
    </div>
  );
}
