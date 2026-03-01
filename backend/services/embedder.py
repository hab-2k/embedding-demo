import logging
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info("Loading sentence-transformers model on device=%s", device)
        _model = SentenceTransformer("all-mpnet-base-v2", device=device)
        logger.info("Model loaded successfully")
    return _model


def embed_texts(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """Embed a list of texts in batches, returning a list of vectors."""
    model = get_model()
    all_embeddings: list[list[float]] = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for i in range(0, len(texts), batch_size):
        batch_num = i // batch_size + 1
        batch = texts[i : i + batch_size]
        embeddings = model.encode(batch, show_progress_bar=False)
        all_embeddings.extend(embeddings.tolist())

        if batch_num % 10 == 0 or batch_num == total_batches:
            logger.info("Embedded batch %d/%d (%d texts so far)", batch_num, total_batches, len(all_embeddings))

    return all_embeddings


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    model = get_model()
    embedding = model.encode([text], show_progress_bar=False)
    return embedding[0].tolist()
