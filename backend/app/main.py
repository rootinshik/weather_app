from fastapi import FastAPI

app = FastAPI(title="Weather Aggregator API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
