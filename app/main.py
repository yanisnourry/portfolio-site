"""FastAPI app: server-rendered pages."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.backtester_client import fetch_results
from app.charts import sparkline_points
from app.config import Settings
from app.formatting import num, pct, utc

BASE_DIR = Path(__file__).resolve().parent

settings = Settings.from_env()

# A public site, not an API: no /docs, /redoc or /openapi.json.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.filters.update(pct=pct, num=num, utc=utc)
templates.env.globals.update(settings=settings)


@app.get("/healthz")
async def healthz():
    # Liveness only: never depends on the backtester being reachable.
    return {"status": "ok"}


@app.get("/")
async def home(request: Request):
    backtest = await fetch_results(settings)
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "page_path": "/",
            "backtest": backtest,
            "sparkline": sparkline_points(backtest.results["equity"]),
        },
    )
