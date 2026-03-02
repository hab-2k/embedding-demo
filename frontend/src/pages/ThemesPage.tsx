import { useEffect, useRef, useState } from "react";
import ClusterScatterPlot from "../components/ClusterScatterPlot";
import TimelineChart from "../components/TimelineChart";
import ThemeCard from "../components/ThemeCard";
import { getThemes } from "../api/client";
import type { Theme } from "../api/client";
import { clusterColor } from "../utils/colors";

export default function ThemesPage() {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [timePeriods, setTimePeriods] = useState<string[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [noiseCount, setNoiseCount] = useState(0);
  const [minClusterSize, setMinClusterSize] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(null);
  const [expandedClusterId, setExpandedClusterId] = useState<number | null>(null);
  const [enhanceWithLlm, setEnhanceWithLlm] = useState(false);
  const [insights, setInsights] = useState<string[]>([]);
  const [llmEnhanced, setLlmEnhanced] = useState(false);

  const cardRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  useEffect(() => {
    setIsLoading(true);
    setError(null);
    getThemes(10, enhanceWithLlm)
      .then((res) => {
        setThemes(res.themes);
        setTimePeriods(res.time_periods);
        setTotalChunks(res.total_chunks);
        setNoiseCount(res.noise_count);
        setMinClusterSize(res.min_cluster_size);
        setInsights(res.insights ?? []);
        setLlmEnhanced(res.llm_enhanced ?? false);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load themes")
      )
      .finally(() => setIsLoading(false));
  }, [enhanceWithLlm]);

  function handleSelectCluster(clusterId: number | null) {
    setSelectedClusterId(clusterId);
    if (clusterId !== null) {
      const el = cardRefs.current.get(clusterId);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-lloyds-black tracking-tight">
          Themes
        </h1>
        <p className="text-sm text-lloyds-grey-dark mt-1">
          Auto-discovered topic clusters via UMAP + HDBSCAN
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <svg
            className="animate-spin h-8 w-8 text-lloyds-green"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!isLoading && !error && themes.length > 0 && (
        <>
          {/* Stats bar */}
          <div className="flex flex-wrap gap-4 mb-6 items-center">
            <div className="bg-white rounded-lg border border-lloyds-grey-mid/50 px-4 py-2.5 shadow-sm">
              <p className="text-xs text-lloyds-grey-dark">Chunks analysed</p>
              <p className="text-lg font-semibold text-lloyds-black">
                {totalChunks}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-lloyds-grey-mid/50 px-4 py-2.5 shadow-sm">
              <p className="text-xs text-lloyds-grey-dark">
                Clusters discovered
              </p>
              <p className="text-lg font-semibold text-lloyds-black">
                {themes.length}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-lloyds-grey-mid/50 px-4 py-2.5 shadow-sm">
              <p className="text-xs text-lloyds-grey-dark">Noise points</p>
              <p className="text-lg font-semibold text-lloyds-black">
                {noiseCount}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-lloyds-grey-mid/50 px-4 py-2.5 shadow-sm">
              <p className="text-xs text-lloyds-grey-dark">Min cluster size</p>
              <p className="text-lg font-semibold text-lloyds-black">
                {minClusterSize}
              </p>
            </div>
            <label className="ml-auto flex items-center gap-2 bg-white rounded-lg border border-lloyds-grey-mid/50 px-4 py-2.5 shadow-sm cursor-pointer select-none">
              <span className="text-xs font-medium text-lloyds-black">
                Enhance with AI
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={enhanceWithLlm}
                onClick={(e) => {
                  e.preventDefault();
                  setEnhanceWithLlm(!enhanceWithLlm);
                }}
                className={`relative inline-flex h-5 w-9 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  enhanceWithLlm ? "bg-lloyds-green" : "bg-lloyds-grey-mid"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                    enhanceWithLlm ? "translate-x-4" : "translate-x-0"
                  }`}
                />
              </button>
              {llmEnhanced && (
                <span className="text-[10px] text-lloyds-green font-medium">
                  Active
                </span>
              )}
            </label>
          </div>

          {/* AI Insights banner */}
          {insights.length > 0 && (
            <div className="mb-6 bg-lloyds-green-50 rounded-xl border border-lloyds-green/20 p-5">
              <h2 className="text-sm font-semibold text-lloyds-green mb-3">
                AI Insights
              </h2>
              <ul className="space-y-1.5">
                {insights.map((insight, i) => (
                  <li
                    key={i}
                    className="text-sm text-lloyds-black/80 leading-relaxed flex gap-2"
                  >
                    <span className="text-lloyds-green shrink-0">-</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Timeline chart */}
          {timePeriods.length > 0 && (
            <div className="mb-8">
              <TimelineChart
                themes={themes}
                timePeriods={timePeriods}
                selectedClusterId={selectedClusterId}
                onSelectCluster={handleSelectCluster}
              />
            </div>
          )}

          {/* Scatter plot */}
          <div className="mb-8">
            <ClusterScatterPlot
              themes={themes}
              selectedClusterId={selectedClusterId}
              onSelectCluster={handleSelectCluster}
            />
          </div>

          {/* Theme cards grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {themes.map((theme, i) => (
              <div
                key={theme.cluster_id}
                ref={(el) => {
                  if (el) cardRefs.current.set(theme.cluster_id, el);
                }}
                className={
                  selectedClusterId === theme.cluster_id
                    ? "ring-2 ring-offset-2 rounded-xl"
                    : ""
                }
                style={
                  selectedClusterId === theme.cluster_id
                    ? { ringColor: clusterColor(i) }
                    : undefined
                }
              >
                <ThemeCard
                  theme={theme}
                  color={clusterColor(i)}
                  isExpanded={expandedClusterId === theme.cluster_id}
                  onToggle={() =>
                    setExpandedClusterId(
                      expandedClusterId === theme.cluster_id
                        ? null
                        : theme.cluster_id
                    )
                  }
                />
              </div>
            ))}
          </div>
        </>
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
