import io
import logging
import time

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from models.schemas import IngestResponse
from services.chunker import chunk_sentences
from services.embedder import embed_texts
from services.vector_store import ensure_collection, transcript_exists, upsert_chunks

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_csv(file: UploadFile = File(...)) -> IngestResponse:
    """Ingest a CSV of transcript sentences, chunk them, embed, and store."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    start_time = time.time()

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    required_cols = {"transcript_id", "transcript_index", "text"}
    if not required_cols.issubset(set(df.columns)):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {required_cols}. Got: {list(df.columns)}",
        )

    df = df.dropna(subset=["text"])
    df["transcript_index"] = df["transcript_index"].astype(int)

    ensure_collection()

    transcript_ids = df["transcript_id"].unique()
    all_chunks: list[dict] = []
    skipped = 0

    for tid in transcript_ids:
        tid_str = str(tid)
        if transcript_exists(tid_str):
            logger.info("Transcript '%s' already indexed, skipping", tid_str)
            skipped += 1
            continue

        sentences = df[df["transcript_id"] == tid].to_dict("records")
        sentences = [
            {"transcript_index": int(s["transcript_index"]), "text": str(s["text"])}
            for s in sentences
        ]
        chunks = chunk_sentences(sentences, tid_str)
        all_chunks.extend(chunks)

    processed = len(transcript_ids) - skipped

    if not all_chunks:
        elapsed = round(time.time() - start_time, 2)
        return IngestResponse(
            chunks_written=0,
            transcripts_processed=processed,
            time_taken_seconds=elapsed,
        )

    texts = [c["text"] for c in all_chunks]
    logger.info("Embedding %d chunks...", len(texts))
    vectors = embed_texts(texts)

    chunks_written = upsert_chunks(all_chunks, vectors)
    elapsed = round(time.time() - start_time, 2)

    logger.info(
        "Ingest complete: %d chunks written, %d transcripts processed, %.2fs",
        chunks_written,
        processed,
        elapsed,
    )

    return IngestResponse(
        chunks_written=chunks_written,
        transcripts_processed=processed,
        time_taken_seconds=elapsed,
    )
