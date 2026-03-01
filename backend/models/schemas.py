from pydantic import BaseModel


class IngestResponse(BaseModel):
    chunks_written: int
    transcripts_processed: int
    time_taken_seconds: float


class SearchResult(BaseModel):
    chunk_id: str
    transcript_id: str
    text: str
    similarity_score: float
    start_index: int
    end_index: int


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str


class ThemeExcerpt(BaseModel):
    chunk_id: str
    transcript_id: str
    text: str


class Theme(BaseModel):
    cluster_id: int
    label: str
    chunk_count: int
    representative_excerpts: list[ThemeExcerpt]


class ThemesResponse(BaseModel):
    themes: list[Theme]
    n_clusters: int


class RiskFlag(BaseModel):
    chunk_id: str
    transcript_id: str
    text: str
    seed_phrase: str
    similarity_score: float
    start_index: int
    end_index: int


class RiskFlagsResponse(BaseModel):
    flags: list[RiskFlag]
    threshold: float
    seed_phrases_used: list[str]


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    chunks_indexed: int
