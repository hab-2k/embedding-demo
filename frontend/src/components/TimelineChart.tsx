import type { Theme } from "../api/client";
import { clusterColor } from "../utils/colors";

interface TimelineChartProps {
  themes: Theme[];
  timePeriods: string[];
  selectedClusterId: number | null;
  onSelectCluster: (clusterId: number | null) => void;
}

const SVG_WIDTH = 700;
const SVG_HEIGHT = 300;
const PAD_LEFT = 50;
const PAD_RIGHT = 20;
const PAD_TOP = 20;
const PAD_BOTTOM = 50;

export default function TimelineChart({
  themes,
  timePeriods,
  selectedClusterId,
  onSelectCluster,
}: TimelineChartProps) {
  if (themes.length === 0 || timePeriods.length === 0) return null;

  const plotW = SVG_WIDTH - PAD_LEFT - PAD_RIGHT;
  const plotH = SVG_HEIGHT - PAD_TOP - PAD_BOTTOM;

  // Max chunk count across all clusters/periods for y-axis scaling
  const maxCount = Math.max(
    ...themes.flatMap((t) => t.timeline.map((tp) => tp.chunk_count)),
    1
  );

  function xPos(i: number): number {
    if (timePeriods.length === 1) return PAD_LEFT + plotW / 2;
    return PAD_LEFT + (i / (timePeriods.length - 1)) * plotW;
  }

  function yPos(count: number): number {
    return PAD_TOP + plotH - (count / maxCount) * plotH;
  }

  // Y-axis tick values
  const yTicks: number[] = [];
  const tickStep = Math.max(1, Math.ceil(maxCount / 5));
  for (let v = 0; v <= maxCount; v += tickStep) {
    yTicks.push(v);
  }

  // X-axis label thinning: show at most ~8 labels
  const labelInterval = Math.max(1, Math.ceil(timePeriods.length / 8));

  return (
    <div className="bg-white rounded-xl border border-lloyds-grey-mid/50 p-4 shadow-sm">
      <p className="text-xs font-medium text-lloyds-grey-dark mb-2">
        Topic volume over time
      </p>
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="w-full h-auto"
        role="img"
        aria-label="Topic timeline chart"
      >
        {/* Y-axis grid + labels */}
        {yTicks.map((v) => (
          <g key={`y-${v}`}>
            <line
              x1={PAD_LEFT}
              x2={SVG_WIDTH - PAD_RIGHT}
              y1={yPos(v)}
              y2={yPos(v)}
              stroke="#e5e7eb"
              strokeWidth={0.5}
            />
            <text
              x={PAD_LEFT - 8}
              y={yPos(v) + 3}
              textAnchor="end"
              fontSize="9"
              fill="#9ca3af"
            >
              {v}
            </text>
          </g>
        ))}

        {/* X-axis labels */}
        {timePeriods.map((label, i) => {
          if (i % labelInterval !== 0) return null;
          return (
            <text
              key={`x-${label}`}
              x={xPos(i)}
              y={SVG_HEIGHT - 10}
              textAnchor="middle"
              fontSize="9"
              fill="#9ca3af"
            >
              {label}
            </text>
          );
        })}

        {/* Lines per cluster */}
        {themes.map((theme, themeIdx) => {
          const color = clusterColor(themeIdx);
          const isSelected = selectedClusterId === theme.cluster_id;
          const isDimmed = selectedClusterId !== null && !isSelected;

          // Build point coordinates from timeline data
          const points = theme.timeline.map((tp, i) => ({
            x: xPos(i),
            y: yPos(tp.chunk_count),
            count: tp.chunk_count,
          }));

          const polylinePoints = points
            .map((p) => `${p.x},${p.y}`)
            .join(" ");

          return (
            <g
              key={theme.cluster_id}
              className="cursor-pointer"
              opacity={isDimmed ? 0.15 : 1}
              onClick={() =>
                onSelectCluster(isSelected ? null : theme.cluster_id)
              }
            >
              <polyline
                points={polylinePoints}
                fill="none"
                stroke={color}
                strokeWidth={isSelected ? 2.5 : 1.5}
                strokeLinejoin="round"
              />
              {points.map((p, i) => (
                <circle
                  key={i}
                  cx={p.x}
                  cy={p.y}
                  r={isSelected ? 4 : 2.5}
                  fill={color}
                >
                  <title>
                    {theme.keywords[0] || `Cluster ${theme.cluster_id}`}:{" "}
                    {p.count} chunks
                  </title>
                </circle>
              ))}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
