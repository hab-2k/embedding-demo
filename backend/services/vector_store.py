import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

logger = logging.getLogger(__name__)

COLLECTION_NAME = "transcripts"
VECTOR_SIZE = 768

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host="localhost", port=6333)
        logger.info("Connected to Qdrant")
    return _client


def ensure_collection() -> None:
    """Create the transcripts collection if it doesn't exist."""
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        logger.info("Created collection '%s'", COLLECTION_NAME)


def transcript_exists(transcript_id: str) -> bool:
    """Check if any chunks for a transcript_id already exist."""
    client = get_client()
    result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id))]
        ),
        limit=1,
    )
    return len(result[0]) > 0


def upsert_chunks(chunks: list[dict], vectors: list[list[float]]) -> int:
    """Insert chunk points into Qdrant. Returns number of points written."""
    client = get_client()
    points = [
        PointStruct(
            id=chunk["chunk_id"],
            vector=vector,
            payload={
                "chunk_id": chunk["chunk_id"],
                "transcript_id": chunk["transcript_id"],
                "text": chunk["text"],
                "start_index": chunk["start_index"],
                "end_index": chunk["end_index"],
                "date": chunk["date"],
            },
        )
        for chunk, vector in zip(chunks, vectors)
    ]

    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)

    return len(points)


def search(vector: list[float], limit: int = 10) -> list[dict]:
    """Search for nearest vectors. Returns list of result dicts."""
    client = get_client()
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit,
    )
    return [
        {
            "chunk_id": hit.payload["chunk_id"],
            "transcript_id": hit.payload["transcript_id"],
            "text": hit.payload["text"],
            "similarity_score": hit.score,
            "start_index": hit.payload["start_index"],
            "end_index": hit.payload["end_index"],
        }
        for hit in response.points
    ]


def get_all_vectors() -> tuple[list[dict], list[list[float]]]:
    """Retrieve all points from the collection. Returns (payloads, vectors)."""
    client = get_client()
    payloads: list[dict] = []
    vectors: list[list[float]] = []

    offset = None
    while True:
        result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            offset=offset,
            with_vectors=True,
        )
        points, next_offset = result

        for point in points:
            payloads.append(point.payload)
            vectors.append(point.vector)

        if next_offset is None:
            break
        offset = next_offset

    return payloads, vectors


def get_chunk_count() -> int:
    """Get total number of indexed chunks."""
    client = get_client()
    try:
        info = client.get_collection(COLLECTION_NAME)
        return info.points_count
    except Exception:
        return 0


def is_connected() -> bool:
    """Check if Qdrant is reachable."""
    try:
        client = get_client()
        client.get_collections()
        return True
    except Exception:
        return False
