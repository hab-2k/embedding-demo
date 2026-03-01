import logging

from fastapi import APIRouter, Query

from models.schemas import RiskFlagsResponse, RiskFlag
from services.embedder import embed_texts
from services.vector_store import search

logger = logging.getLogger(__name__)
router = APIRouter()

SEED_PHRASES = [
    "I can't afford this",
    "I want to make a complaint",
    "Nobody is helping me",
    "I don't understand what I'm being charged",
    "I'm really struggling financially",
]


@router.get("/risk-flags", response_model=RiskFlagsResponse)
async def get_risk_flags(
    threshold: float = Query(0.75, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=500),
) -> RiskFlagsResponse:
    """Find transcript chunks similar to vulnerability/complaint seed phrases."""
    seed_vectors = embed_texts(SEED_PHRASES)

    seen_chunks: dict[str, RiskFlag] = {}

    for phrase, vector in zip(SEED_PHRASES, seed_vectors):
        results = search(vector, limit=limit)
        for r in results:
            if r["similarity_score"] < threshold:
                continue

            chunk_id = r["chunk_id"]
            flag = RiskFlag(
                chunk_id=chunk_id,
                transcript_id=r["transcript_id"],
                text=r["text"],
                seed_phrase=phrase,
                similarity_score=round(r["similarity_score"], 4),
                start_index=r["start_index"],
                end_index=r["end_index"],
            )

            if chunk_id not in seen_chunks or flag.similarity_score > seen_chunks[chunk_id].similarity_score:
                seen_chunks[chunk_id] = flag

    flags = sorted(seen_chunks.values(), key=lambda f: f.similarity_score, reverse=True)[:limit]

    return RiskFlagsResponse(
        flags=flags,
        threshold=threshold,
        seed_phrases_used=SEED_PHRASES,
    )
