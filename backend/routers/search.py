from fastapi import APIRouter, Query

from models.schemas import SearchResponse, SearchResult
from services.embedder import embed_query
from services.vector_store import search

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_transcripts(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
) -> SearchResponse:
    """Semantic search over transcript chunks."""
    vector = embed_query(q)
    raw_results = search(vector, limit=limit)

    results = [
        SearchResult(
            chunk_id=r["chunk_id"],
            transcript_id=r["transcript_id"],
            text=r["text"],
            similarity_score=round(r["similarity_score"], 4),
            start_index=r["start_index"],
            end_index=r["end_index"],
        )
        for r in raw_results
    ]

    return SearchResponse(results=results, query=q)
