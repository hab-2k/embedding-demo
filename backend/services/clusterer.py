import logging
from collections import defaultdict
from datetime import datetime, timedelta

import hdbscan
import numpy as np
import umap
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


def cluster_chunks(
    texts: list[str],
    vectors: list[list[float]],
    dates: list[str],
    min_cluster_size: int = 10,
    top_n_keywords: int = 5,
) -> dict:
    """Run UMAP + HDBSCAN + c-TF-IDF on transcript chunks.

    Returns dict with keys:
        labels          - int array of cluster labels (-1 = noise)
        embeddings_2d   - Nx2 array of UMAP 2D coordinates
        keywords        - dict[int, list[str]] of top keywords per cluster
        centroids_2d    - dict[int, tuple[float, float]] mean 2D coord per cluster
        unique_labels   - sorted list of cluster ids (excluding -1)
    """
    n_chunks = len(texts)
    min_required = max(min_cluster_size, 20)
    if n_chunks < min_required:
        raise ValueError(
            f"Need at least {min_required} chunks for clustering, got {n_chunks}."
        )

    X = np.array(vectors)

    logger.info("UMAP: reducing %d vectors from 768D to 5D for clustering", n_chunks)
    reducer_5d = umap.UMAP(
        n_components=5, min_dist=0.0, metric="cosine", random_state=42
    )
    embeddings_5d = reducer_5d.fit_transform(X)

    logger.info("UMAP: reducing to 2D for visualisation")
    reducer_2d = umap.UMAP(
        n_components=2, min_dist=0.1, metric="cosine", random_state=42
    )
    embeddings_2d = reducer_2d.fit_transform(X)

    logger.info("HDBSCAN: clustering with min_cluster_size=%d", min_cluster_size)
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size, cluster_selection_method="eom"
    )
    labels = clusterer.fit_predict(embeddings_5d)
    probabilities = clusterer.probabilities_

    unique_labels = sorted(set(labels) - {-1})
    logger.info(
        "Found %d clusters (%d noise points)",
        len(unique_labels),
        int((labels == -1).sum()),
    )

    # c-TF-IDF: join all chunk texts per cluster, then TF-IDF across clusters
    keywords: dict[int, list[str]] = {}
    if unique_labels:
        cluster_docs = []
        cluster_order = []
        for cid in unique_labels:
            member_texts = [texts[i] for i in range(n_chunks) if labels[i] == cid]
            cluster_docs.append(" ".join(member_texts))
            cluster_order.append(cid)

        tfidf = TfidfVectorizer(
            stop_words="english", ngram_range=(2, 3), max_df=0.85
        )
        tfidf_matrix = tfidf.fit_transform(cluster_docs)
        feature_names = tfidf.get_feature_names_out()

        for idx, cid in enumerate(cluster_order):
            row = tfidf_matrix[idx].toarray().flatten()
            top_indices = row.argsort()[::-1][:top_n_keywords]
            keywords[cid] = [feature_names[i] for i in top_indices if row[i] > 0]

    # 2D centroids per cluster
    centroids_2d: dict[int, tuple[float, float]] = {}
    for cid in unique_labels:
        mask = labels == cid
        cx = float(embeddings_2d[mask, 0].mean())
        cy = float(embeddings_2d[mask, 1].mean())
        centroids_2d[cid] = (cx, cy)

    # Temporal analysis: bucket chunks by time period per cluster
    parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    min_date = min(parsed_dates)
    max_date = max(parsed_dates)
    date_range_days = (max_date - min_date).days

    if date_range_days <= 90:
        # Weekly buckets
        def bucket_key(dt: datetime) -> str:
            return dt.strftime("%G-W%V")
    else:
        # Monthly buckets
        def bucket_key(dt: datetime) -> str:
            return dt.strftime("%Y-%m")

    # Build sorted list of all time periods
    all_buckets: set[str] = set()
    chunk_buckets = [bucket_key(d) for d in parsed_dates]
    all_buckets.update(chunk_buckets)

    # Generate complete period range to fill gaps
    cursor = min_date
    while cursor <= max_date:
        all_buckets.add(bucket_key(cursor))
        cursor += timedelta(days=7 if date_range_days <= 90 else 30)
    time_periods = sorted(all_buckets)

    # Count chunks per bucket per cluster
    timelines: dict[int, list[tuple[str, int]]] = {}
    for cid in unique_labels:
        counts: dict[str, int] = defaultdict(int)
        for i in range(n_chunks):
            if labels[i] == cid:
                counts[chunk_buckets[i]] += 1
        timelines[cid] = [(p, counts.get(p, 0)) for p in time_periods]

    return {
        "labels": labels,
        "probabilities": probabilities,
        "embeddings_2d": embeddings_2d,
        "embeddings_5d": embeddings_5d,
        "keywords": keywords,
        "centroids_2d": centroids_2d,
        "unique_labels": unique_labels,
        "timelines": timelines,
        "time_periods": time_periods,
    }
