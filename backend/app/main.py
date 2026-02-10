import logging

from fastapi import FastAPI

from app.services.source_manager import source_manager

logger = logging.getLogger(__name__)

app = FastAPI(title="Weather Aggregator API")


@app.on_event("startup")
async def startup() -> None:
    source_manager.load()
    logger.info("Source configs loaded: %d sources", len(source_manager.get_all()))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
