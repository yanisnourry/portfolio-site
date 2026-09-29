"""FastAPI app: server-rendered pages."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

# A public site, not an API: no /docs, /redoc or /openapi.json.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/healthz")
async def healthz():
    # Liveness only: never depends on the backtester being reachable.
    return {"status": "ok"}
