import asyncio
import logging
from collections import defaultdict

import numpy as np
from fastapi import APIRouter, Query, HTTPException
from sklearn.feature_extraction.text import TfidfVectorizer

from models.schemas import ThemesResponse, Theme, ThemeExcerpt, TimelinePoint
from services import llm, theme_cache
from services.cluster_refiner import refine_clusters
from services.clusterer import cluster_chunks
from services.vector_store import get_all_vectors

logger = logging.getLogger(__name__)
router = APIRouter()

# Gate concurrent LLM calls to avoid 429 rate-limits from the API
_llm_semaphore = asyncio.Semaphore(2)


async def _llm_call(messages: list[dict], **kwargs) -> str:
    """Run llm.chat_completion through a concurrency-limiting semaphore."""
    async with _llm_semaphore:
        return await asyncio.to_thread(llm.chat_completion, messages, **kwargs)


async def generate_cluster_name(keywords: list[str], excerpts: list[str]) -> str:
    """Ask the LLM for a concise 3-7 word topic name for a cluster."""
    prompt = (
        "Given these TF-IDF keywords and sample transcript excerpts from a UK bank "
        "call centre, produce a concise 3-7 word topic name for this customer service "
        "call cluster. Return ONLY the topic name, nothing else.\n\n"
        f"Keywords: {', '.join(keywords)}\n\n"
        "Excerpts:\n" + "\n".join(f"- {e[:200]}" for e in excerpts[:5])
    )
    try:
        name = await _llm_call(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=32,
        )
        return name.strip().strip('"').strip("'")
    except Exception:
        logger.warning("LLM cluster naming failed, falling back to keywords")
        return ", ".join(keywords) if keywords else "Unknown Topic"


async def generate_trend_insights(themes_summary: list[dict]) -> list[str]:
    """Generate 3-5 executive-level bullet points about trends across all clusters."""
    summary_text = "\n".join(
        f"- {t['name']} ({t['chunk_count']} chunks, {t['pct_of_total']:.1f}% of total, "
        f"trend: {t['trend_direction']})"
        for t in themes_summary
    )
    prompt = (
        "You are a call centre analytics analyst at a UK retail bank. Given these "
        "topic clusters and their volume trends, write 3-5 concise bullet-point "
        "insights for a weekly executive summary. Focus on notable changes, emerging "
        "risks, and actionable observations.\n\n"
        f"Clusters:\n{summary_text}\n\n"
        "Return ONLY the bullet points, one per line, starting with a dash (-)."
    )
    try:
        response = await _llm_call(
            [{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=512,
        )
        bullets = [
            line.strip().lstrip("-").strip()
            for line in response.strip().splitlines()
            if line.strip().startswith("-")
        ]
        return bullets[:5] if bullets else [response.strip()]
    except Exception:
        logger.warning("LLM trend insights generation failed")
        return []


def _compute_trend_direction(timeline: list[tuple[str, int]]) -> str:
    """Compare the last period's count to the mean to determine trend."""
    if len(timeline) < 2:
        return "stable"
    counts = [c for _, c in timeline]
    mean_count = sum(counts) / len(counts)
    last_count = counts[-1]
    if mean_count == 0:
        return "stable"
    ratio = last_count / mean_count
    if ratio > 1.3:
        return "increasing"
    elif ratio < 0.7:
        return "decreasing"
    return "stable"


def _recompute_cluster_data(
    labels: np.ndarray,
    texts: list[str],
    embeddings_2d: np.ndarray,
    dates: list[str],
    top_n_keywords: int,
) -> dict:
    """Re-derive keywords, centroids, timelines from updated labels."""
    from datetime import datetime, timedelta

    n_chunks = len(texts)
    unique_labels = sorted(set(labels) - {-1})

    # c-TF-IDF
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

    # 2D centroids
    centroids_2d: dict[int, tuple[float, float]] = {}
    for cid in unique_labels:
        mask = labels == cid
        cx = float(embeddings_2d[mask, 0].mean())
        cy = float(embeddings_2d[mask, 1].mean())
        centroids_2d[cid] = (cx, cy)

    # Timelines
    parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    min_date = min(parsed_dates)
    max_date = max(parsed_dates)
    date_range_days = (max_date - min_date).days

    if date_range_days <= 90:
        def bucket_key(dt: datetime) -> str:
            return dt.strftime("%G-W%V")
    else:
        def bucket_key(dt: datetime) -> str:
            return dt.strftime("%Y-%m")

    all_buckets: set[str] = set()
    chunk_buckets = [bucket_key(d) for d in parsed_dates]
    all_buckets.update(chunk_buckets)

    cursor = min_date
    while cursor <= max_date:
        all_buckets.add(bucket_key(cursor))
        cursor += timedelta(days=7 if date_range_days <= 90 else 30)
    time_periods = sorted(all_buckets)

    timelines: dict[int, list[tuple[str, int]]] = {}
    for cid in unique_labels:
        counts: dict[str, int] = defaultdict(int)
        for i in range(n_chunks):
            if labels[i] == cid:
                counts[chunk_buckets[i]] += 1
        timelines[cid] = [(p, counts.get(p, 0)) for p in time_periods]

    return {
        "keywords": keywords,
        "centroids_2d": centroids_2d,
        "unique_labels": unique_labels,
        "timelines": timelines,
        "time_periods": time_periods,
    }


def _build_themes(
    unique_labels: list[int],
    labels: np.ndarray,
    embeddings_2d: np.ndarray,
    centroids_2d: dict[int, tuple[float, float]],
    keywords: dict[int, list[str]],
    timelines: dict[int, list[tuple[str, int]]],
    payloads: list[dict],
) -> list[Theme]:
    """Build sorted Theme objects from clustering results."""
    themes: list[Theme] = []
    for cid in unique_labels:
        mask = labels == cid
        member_indices = np.where(mask)[0]

        cx, cy = centroids_2d[cid]
        member_2d = embeddings_2d[member_indices]
        centroid_2d = np.array([cx, cy])
        distances = np.linalg.norm(member_2d - centroid_2d, axis=1)
        nearest = np.argsort(distances)[:5]

        excerpts: list[ThemeExcerpt] = []
        for rank in nearest:
            global_idx = member_indices[rank]
            p = payloads[global_idx]
            excerpts.append(
                ThemeExcerpt(
                    chunk_id=p["chunk_id"],
                    transcript_id=p["transcript_id"],
                    text=p["text"],
                    x=float(embeddings_2d[global_idx, 0]),
                    y=float(embeddings_2d[global_idx, 1]),
                    date=p["date"],
                )
            )

        kw = keywords.get(cid, [])
        timeline = [
            TimelinePoint(period=period, chunk_count=count)
            for period, count in timelines.get(cid, [])
        ]
        themes.append(
            Theme(
                cluster_id=cid,
                label=", ".join(kw) if kw else f"Cluster {cid}",
                keywords=kw,
                chunk_count=int(mask.sum()),
                x=cx,
                y=cy,
                representative_excerpts=excerpts,
                timeline=timeline,
            )
        )

    themes.sort(key=lambda t: t.chunk_count, reverse=True)
    return themes


@router.get("/themes", response_model=ThemesResponse)
async def get_themes(
    min_cluster_size: int = Query(10, ge=3, le=100),
    top_n_keywords: int = Query(5, ge=1, le=10),
    enhance_with_llm: bool = Query(False),
    large_cluster_factor: float = Query(2.0, ge=1.0, le=10.0),
    coherence_threshold: float = Query(0.65, ge=0.0, le=1.0),
    merge_similarity_threshold: float = Query(0.85, ge=0.5, le=1.0),
) -> ThemesResponse:
    """Cluster all transcript chunks and optionally enhance with LLM."""
    params = {
        "min_cluster_size": min_cluster_size,
        "top_n_keywords": top_n_keywords,
        "enhance_with_llm": enhance_with_llm,
        "large_cluster_factor": large_cluster_factor,
        "coherence_threshold": coherence_threshold,
        "merge_similarity_threshold": merge_similarity_threshold,
    }

    cached = theme_cache.get_cached(params)
    if cached is not None:
        return ThemesResponse(**cached)

    payloads, vectors = get_all_vectors()
    total_chunks = len(payloads)
    texts = [p["text"] for p in payloads]
    dates = [p["date"] for p in payloads]

    try:
        result = cluster_chunks(
            texts=texts,
            vectors=vectors,
            dates=dates,
            min_cluster_size=min_cluster_size,
            top_n_keywords=top_n_keywords,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    labels = result["labels"]
    embeddings_2d = result["embeddings_2d"]
    embeddings_5d = result["embeddings_5d"]
    keywords = result["keywords"]
    centroids_2d = result["centroids_2d"]
    unique_labels = result["unique_labels"]
    timelines = result["timelines"]
    time_periods = result["time_periods"]
    probabilities = result["probabilities"]

    noise_count = int((labels == -1).sum())
    llm_enhanced = False
    insights: list[str] = []

    # Build themes from initial clusters
    themes = _build_themes(
        unique_labels, labels, embeddings_2d, centroids_2d,
        keywords, timelines, payloads,
    )

    if enhance_with_llm and llm.is_configured():
        llm_enhanced = True

        # --- Priority 1: Name all clusters concurrently ---
        try:
            name_tasks = [
                generate_cluster_name(
                    t.keywords, [e.text for e in t.representative_excerpts]
                )
                for t in themes
            ]
            names = await asyncio.gather(*name_tasks)
            for theme, name in zip(themes, names):
                theme.summary = name
                theme.label = name
        except Exception:
            logger.warning("LLM naming failed, keeping keyword labels")

        # --- Priority 2: Trend insights (single LLM call across all clusters) ---
        themes_summary = []
        for theme in themes:
            raw_timeline = timelines.get(theme.cluster_id, [])
            trend = _compute_trend_direction(raw_timeline)
            themes_summary.append({
                "name": theme.summary or theme.label,
                "chunk_count": theme.chunk_count,
                "pct_of_total": (theme.chunk_count / total_chunks * 100)
                if total_chunks
                else 0,
                "trend_direction": trend,
            })

        try:
            insights = await generate_trend_insights(themes_summary)
        except Exception:
            logger.warning("LLM trend insights failed")

        # --- Last: Optional merge/split refinement (single pass, max 3 merge checks) ---
        try:
            refined_labels = await refine_clusters(
                labels=labels,
                embeddings_5d=embeddings_5d,
                texts=texts,
                keywords=keywords,
                probabilities=probabilities,
                large_cluster_factor=large_cluster_factor,
                coherence_threshold=coherence_threshold,
                merge_similarity_threshold=merge_similarity_threshold,
            )

            if not np.array_equal(refined_labels, labels):
                labels = refined_labels
                noise_count = int((labels == -1).sum())
                recomputed = _recompute_cluster_data(
                    labels, texts, embeddings_2d, dates, top_n_keywords
                )
                themes = _build_themes(
                    recomputed["unique_labels"], labels, embeddings_2d,
                    recomputed["centroids_2d"], recomputed["keywords"],
                    recomputed["timelines"], payloads,
                )
                time_periods = recomputed["time_periods"]

                # Re-name only the new/changed clusters
                name_tasks = [
                    generate_cluster_name(
                        t.keywords, [e.text for e in t.representative_excerpts]
                    )
                    for t in themes
                ]
                new_names = await asyncio.gather(*name_tasks)
                for theme, name in zip(themes, new_names):
                    theme.summary = name
                    theme.label = name
        except Exception:
            logger.warning("Cluster refinement failed, using pre-refinement themes")

    response = ThemesResponse(
        themes=themes,
        total_chunks=total_chunks,
        noise_count=noise_count,
        min_cluster_size=min_cluster_size,
        time_periods=time_periods,
        insights=insights,
        llm_enhanced=llm_enhanced,
    )

    theme_cache.set_cached(params, response.model_dump())

    return response
