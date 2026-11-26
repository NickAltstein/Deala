"""Deala HTTP service. It only receives webhooks; it does not run the sidecar."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.webhooks import router
from app.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Deala", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
