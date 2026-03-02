const CLUSTER_COLORS = [
  "#006A4A", // Fun Green (primary)
  "#00876E", // teal
  "#2E8B57", // sea green
  "#3CB371", // medium sea green
  "#008B8B", // dark cyan
  "#20B2AA", // light sea green
  "#4A9E7D", // muted green
  "#1B7A5A", // deep green
  "#5FAD8C", // sage
  "#0D9B76", // emerald
  "#377E62", // forest
  "#6DBFA0", // mint
];

export function clusterColor(index: number): string {
  return CLUSTER_COLORS[index % CLUSTER_COLORS.length];
}
