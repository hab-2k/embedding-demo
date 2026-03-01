import logging

import numpy as np
from fastapi import APIRouter, Query, HTTPException
from sklearn.cluster import KMeans

from models.schemas import ThemesResponse, Theme, ThemeExcerpt
from services.vector_store import get_all_vectors

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/themes", response_model=ThemesResponse)
async def get_themes(
    n_clusters: int = Query(8, ge=2, le=50),
) -> ThemesResponse:
    """Cluster all transcript chunks and return theme summaries."""
    payloads, vectors = get_all_vectors()

    if len(payloads) < n_clusters:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough data to form {n_clusters} clusters. Only {len(payloads)} chunks indexed.",
        )

    X = np.array(vectors)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    themes: list[Theme] = []
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        cluster_indices = np.where(mask)[0]
        cluster_vectors = X[mask]
        centroid = kmeans.cluster_centers_[cluster_id]

        distances = np.linalg.norm(cluster_vectors - centroid, axis=1)
        sorted_local = np.argsort(distances)

        representative_idx = cluster_indices[sorted_local[0]]
        label_text = payloads[representative_idx]["text"]
        label = label_text[:100].strip()

        excerpts: list[ThemeExcerpt] = []
        for rank in sorted_local[:5]:
            global_idx = cluster_indices[rank]
            p = payloads[global_idx]
            excerpts.append(
                ThemeExcerpt(
                    chunk_id=p["chunk_id"],
                    transcript_id=p["transcript_id"],
                    text=p["text"],
                )
            )

        themes.append(
            Theme(
                cluster_id=cluster_id,
                label=label,
                chunk_count=int(mask.sum()),
                representative_excerpts=excerpts,
            )
        )

    return ThemesResponse(themes=themes, n_clusters=n_clusters)
