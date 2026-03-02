import uuid


def chunk_sentences(
    sentences: list[dict],
    transcript_id: str,
    date: str,
    chunk_size: int = 6,
    step_size: int = 3,
) -> list[dict]:
    """Group sentences into overlapping chunks using a sliding window.

    Args:
        sentences: List of dicts with 'transcript_index' and 'text' keys,
                   sorted by transcript_index.
        transcript_id: The transcript these sentences belong to.
        chunk_size: Number of sentences per chunk.
        step_size: Sliding window step (chunk_size / 2 for 50% overlap).

    Returns:
        List of chunk dicts ready for embedding and storage.
    """
    if not sentences:
        return []

    sorted_sentences = sorted(sentences, key=lambda s: s["transcript_index"])
    chunks: list[dict] = []

    for i in range(0, len(sorted_sentences), step_size):
        window = sorted_sentences[i : i + chunk_size]
        if not window:
            break

        chunk_text = " ".join(s["text"] for s in window)
        start_index = window[0]["transcript_index"]
        end_index = window[-1]["transcript_index"]

        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "transcript_id": transcript_id,
            "text": chunk_text,
            "start_index": start_index,
            "end_index": end_index,
            "date": date,
        })

    return chunks
