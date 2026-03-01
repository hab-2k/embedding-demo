import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import HealthResponse
from routers import ingest, search, themes, risk
from services.vector_store import is_connected, get_chunk_count, ensure_collection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Transcript Semantic Search", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(themes.router)
app.include_router(risk.router)


@app.on_event("startup")
async def startup() -> None:
    ensure_collection()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    connected = is_connected()
    count = get_chunk_count() if connected else 0
    return HealthResponse(
        status="ok",
        qdrant="connected" if connected else "disconnected",
        chunks_indexed=count,
    )
