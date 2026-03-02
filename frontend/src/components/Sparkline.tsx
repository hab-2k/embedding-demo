interface SparklineProps {
  data: number[];
  color: string;
  width?: number;
  height?: number;
}

export default function Sparkline({
  data,
  color,
  width = 80,
  height = 24,
}: SparklineProps) {
  if (data.length < 2) return null;

  const max = Math.max(...data, 1);
  const padY = 2;
  const plotH = height - padY * 2;

  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = padY + plotH - (v / max) * plotH;
    return `${x},${y}`;
  });

  const polyline = points.join(" ");
  const areaPath = `M${points[0]} ${points.slice(1).map((p) => `L${p}`).join(" ")} L${width},${height} L0,${height} Z`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="inline-block"
    >
      <path d={areaPath} fill={color} fillOpacity={0.2} />
      <polyline
        points={polyline}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
    </svg>
  );
}
