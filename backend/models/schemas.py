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


class TimelinePoint(BaseModel):
    period: str
    chunk_count: int


class ThemeExcerpt(BaseModel):
    chunk_id: str
    transcript_id: str
    text: str
    x: float
    y: float
    date: str


class Theme(BaseModel):
    cluster_id: int
    label: str
    keywords: list[str]
    chunk_count: int
    x: float
    y: float
    representative_excerpts: list[ThemeExcerpt]
    timeline: list[TimelinePoint]
    summary: str = ""


class ThemesResponse(BaseModel):
    themes: list[Theme]
    total_chunks: int
    noise_count: int
    min_cluster_size: int
    time_periods: list[str]
    insights: list[str] = []
    llm_enhanced: bool = False


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
