const BASE_URL = "http://localhost:8000";

export interface IngestResponse {
  chunks_written: number;
  transcripts_processed: number;
  time_taken_seconds: number;
}

export interface SearchResult {
  chunk_id: string;
  transcript_id: string;
  text: string;
  similarity_score: number;
  start_index: number;
  end_index: number;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
}

export interface TimelinePoint {
  period: string;
  chunk_count: number;
}

export interface ThemeExcerpt {
  chunk_id: string;
  transcript_id: string;
  text: string;
  x: number;
  y: number;
  date: string;
}

export interface Theme {
  cluster_id: number;
  label: string;
  keywords: string[];
  chunk_count: number;
  x: number;
  y: number;
  representative_excerpts: ThemeExcerpt[];
  timeline: TimelinePoint[];
  summary: string;
}

export interface ThemesResponse {
  themes: Theme[];
  total_chunks: number;
  noise_count: number;
  min_cluster_size: number;
  time_periods: string[];
  insights: string[];
  llm_enhanced: boolean;
}

export interface RiskFlag {
  chunk_id: string;
  transcript_id: string;
  text: string;
  seed_phrase: string;
  similarity_score: number;
  start_index: number;
  end_index: number;
}

export interface RiskFlagsResponse {
  flags: RiskFlag[];
  threshold: number;
  seed_phrases_used: string[];
}

export interface HealthResponse {
  status: string;
  qdrant: string;
  chunks_indexed: number;
}

export async function ingestCSV(file: File): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/ingest`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Ingest failed");
  }
  return res.json();
}

export async function searchTranscripts(
  query: string,
  limit: number = 10
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  const res = await fetch(`${BASE_URL}/search?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Search failed");
  }
  return res.json();
}

export async function getThemes(
  minClusterSize: number = 10,
  enhanceWithLlm: boolean = false
): Promise<ThemesResponse> {
  const params = new URLSearchParams({
    min_cluster_size: String(minClusterSize),
    enhance_with_llm: String(enhanceWithLlm),
  });
  const res = await fetch(`${BASE_URL}/themes?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to load themes");
  }
  return res.json();
}

export async function getRiskFlags(
  threshold: number = 0.75,
  limit: number = 50
): Promise<RiskFlagsResponse> {
  const params = new URLSearchParams({
    threshold: String(threshold),
    limit: String(limit),
  });
  const res = await fetch(`${BASE_URL}/risk-flags?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to load risk flags");
  }
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) {
    throw new Error("Health check failed");
  }
  return res.json();
}
