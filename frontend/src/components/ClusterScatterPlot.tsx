import type { Theme } from "../api/client";
import { clusterColor } from "../utils/colors";

interface ClusterScatterPlotProps {
  themes: Theme[];
  selectedClusterId: number | null;
  onSelectCluster: (clusterId: number | null) => void;
}

const SVG_WIDTH = 600;
const SVG_HEIGHT = 400;
const PADDING = 60;

export default function ClusterScatterPlot({
  themes,
  selectedClusterId,
  onSelectCluster,
}: ClusterScatterPlotProps) {
  if (themes.length === 0) return null;

  // Compute bounds from theme centroids
  const xs = themes.map((t) => t.x);
  const ys = themes.map((t) => t.y);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);

  const xRange = xMax - xMin || 1;
  const yRange = yMax - yMin || 1;

  function scaleX(x: number): number {
    return PADDING + ((x - xMin) / xRange) * (SVG_WIDTH - 2 * PADDING);
  }

  function scaleY(y: number): number {
    return PADDING + ((y - yMin) / yRange) * (SVG_HEIGHT - 2 * PADDING);
  }

  // Bubble radius based on chunk count
  const maxCount = Math.max(...themes.map((t) => t.chunk_count));
  function bubbleRadius(count: number): number {
    return 12 + (Math.sqrt(count / maxCount)) * 28;
  }

  return (
    <div className="bg-white rounded-xl border border-lloyds-grey-mid/50 p-4 shadow-sm">
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="w-full h-auto"
        role="img"
        aria-label="Cluster scatter plot"
      >
        {themes.map((theme, i) => {
          const cx = scaleX(theme.x);
          const cy = scaleY(theme.y);
          const r = bubbleRadius(theme.chunk_count);
          const color = clusterColor(i);
          const isSelected = selectedClusterId === theme.cluster_id;
          const isDimmed = selectedClusterId !== null && !isSelected;

          return (
            <g
              key={theme.cluster_id}
              className="cursor-pointer"
              onClick={() =>
                onSelectCluster(isSelected ? null : theme.cluster_id)
              }
            >
              <circle
                cx={cx}
                cy={cy}
                r={r}
                fill={color}
                fillOpacity={isDimmed ? 0.2 : 0.5}
                stroke={isSelected ? color : "none"}
                strokeWidth={isSelected ? 3 : 0}
              >
                <title>
                  {theme.label} ({theme.chunk_count} chunks)
                </title>
              </circle>
              <text
                x={cx}
                y={cy + r + 14}
                textAnchor="middle"
                fontSize="10"
                fill={isDimmed ? "#999" : "#333"}
                className="pointer-events-none select-none"
              >
                {theme.keywords[0] || `Cluster ${theme.cluster_id}`}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
