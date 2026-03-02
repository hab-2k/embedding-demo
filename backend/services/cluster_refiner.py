import asyncio
import logging

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from services import llm

logger = logging.getLogger(__name__)

# Shared semaphore with themes router — limit concurrent LLM calls
_llm_semaphore = asyncio.Semaphore(2)


async def _llm_call(messages: list[dict], **kwargs) -> str:
    async with _llm_semaphore:
        return await asyncio.to_thread(llm.chat_completion, messages, **kwargs)


def compute_coherence(
    labels: np.ndarray, probabilities: np.ndarray
) -> dict[int, float]:
    """Mean HDBSCAN membership probability per cluster. Range 0-1."""
    coherence: dict[int, float] = {}
    for cid in sorted(set(labels) - {-1}):
        mask = labels == cid
        coherence[cid] = float(probabilities[mask].mean())
    return coherence


async def check_split(
    cluster_id: int,
    keywords: list[str],
    excerpts: list[str],
) -> bool:
    """Ask the LLM whether a cluster should be split. Returns True if split recommended."""
    prompt = (
        f"This cluster of transcript chunks has keywords: {', '.join(keywords)}.\n"
        f"Sample excerpts:\n"
        + "\n".join(f"- {e[:200]}" for e in excerpts[:5])
        + "\n\nIs this a single coherent topic, or should it be split into 2 subtopics? "
        "Answer only SPLIT or KEEP."
    )
    try:
        response = await _llm_call(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=64,
        )
        return "SPLIT" in response.upper()
    except Exception:
        logger.warning("LLM split check failed for cluster %d, keeping", cluster_id)
        return False


async def check_merge(
    cluster_a_keywords: list[str],
    cluster_b_keywords: list[str],
) -> bool:
    """Ask the LLM whether two clusters should be merged. Returns True if merge recommended."""
    prompt = (
        f"Cluster A keywords: {', '.join(cluster_a_keywords)}\n"
        f"Cluster B keywords: {', '.join(cluster_b_keywords)}\n\n"
        "Are these the same topic? Answer only YES or NO."
    )
    try:
        response = await _llm_call(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=16,
        )
        return "YES" in response.upper()
    except Exception:
        logger.warning("LLM merge check failed, skipping merge")
        return False


def _split_cluster(
    labels: np.ndarray,
    embeddings_5d: np.ndarray,
    cluster_id: int,
) -> np.ndarray:
    """Split a cluster into two sub-clusters using KMeans on 5D embeddings."""
    mask = labels == cluster_id
    indices = np.where(mask)[0]
    sub_embeddings = embeddings_5d[indices]

    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    sub_labels = kmeans.fit_predict(sub_embeddings)

    new_id = labels.max() + 1
    new_labels = labels.copy()
    # Keep sub-cluster 0 as original cluster_id, assign sub-cluster 1 a new id
    for i, idx in enumerate(indices):
        if sub_labels[i] == 1:
            new_labels[idx] = new_id

    return new_labels


_MAX_MERGE_CANDIDATES = 3


async def refine_clusters(
    labels: np.ndarray,
    embeddings_5d: np.ndarray,
    texts: list[str],
    keywords: dict[int, list[str]],
    probabilities: np.ndarray,
    large_cluster_factor: float = 2.0,
    coherence_threshold: float = 0.65,
    merge_similarity_threshold: float = 0.85,
) -> np.ndarray:
    """Refine cluster assignments using LLM-guided merge/split decisions.

    Runs a single pass: splits first, then up to 3 merge checks.
    Returns modified labels array.
    """
    labels = labels.copy()
    unique_labels = sorted(set(labels) - {-1})
    if not unique_labels:
        return labels

    # --- Split phase ---
    coherence = compute_coherence(labels, probabilities)
    cluster_sizes = {
        cid: int((labels == cid).sum()) for cid in unique_labels
    }
    median_size = float(np.median(list(cluster_sizes.values())))

    split_candidates = [
        cid
        for cid in unique_labels
        if cluster_sizes[cid] > median_size * large_cluster_factor
        or coherence.get(cid, 1.0) < coherence_threshold
    ]

    if split_candidates:
        split_tasks = []
        for cid in split_candidates:
            cid_indices = np.where(labels == cid)[0]
            cid_texts = [texts[i] for i in cid_indices[:5]]
            cid_kw = keywords.get(cid, [])
            split_tasks.append(check_split(cid, cid_kw, cid_texts))

        split_results = await asyncio.gather(*split_tasks)

        for cid, should_split in zip(split_candidates, split_results):
            if should_split and int((labels == cid).sum()) >= 6:
                logger.info(
                    "Splitting cluster %d (%d chunks)",
                    cid,
                    int((labels == cid).sum()),
                )
                labels = _split_cluster(labels, embeddings_5d, cid)

    # --- Merge phase (capped at _MAX_MERGE_CANDIDATES checks) ---
    unique_labels = sorted(set(labels) - {-1})
    if len(unique_labels) < 2:
        return labels

    centroids_5d = {}
    for cid in unique_labels:
        mask = labels == cid
        centroids_5d[cid] = embeddings_5d[mask].mean(axis=0)

    centroid_matrix = np.array([centroids_5d[cid] for cid in unique_labels])
    sim_matrix = cosine_similarity(centroid_matrix)

    merge_candidates = []
    for i in range(len(unique_labels)):
        for j in range(i + 1, len(unique_labels)):
            if sim_matrix[i, j] > merge_similarity_threshold:
                merge_candidates.append(
                    (unique_labels[i], unique_labels[j], sim_matrix[i, j])
                )

    # Keep only the top pairs by similarity
    merge_candidates.sort(key=lambda x: x[2], reverse=True)
    merge_candidates = merge_candidates[:_MAX_MERGE_CANDIDATES]

    if merge_candidates:
        logger.info("Checking %d merge candidates", len(merge_candidates))
        merge_tasks = [
            check_merge(keywords.get(a, []), keywords.get(b, []))
            for a, b, _ in merge_candidates
        ]
        merge_results = await asyncio.gather(*merge_tasks)

        for (cid_a, cid_b, _), should_merge in zip(
            merge_candidates, merge_results
        ):
            if should_merge:
                size_a = int((labels == cid_a).sum())
                size_b = int((labels == cid_b).sum())
                if size_a >= size_b:
                    labels[labels == cid_b] = cid_a
                    logger.info("Merged cluster %d into %d", cid_b, cid_a)
                else:
                    labels[labels == cid_a] = cid_b
                    logger.info("Merged cluster %d into %d", cid_a, cid_b)

    return labels
