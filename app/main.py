"""FastAPI app: server-rendered pages."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.backtester_client import fetch_results
from app.charts import equity_chart
from app.config import Settings
from app.formatting import day, num, pct, utc

BASE_DIR = Path(__file__).resolve().parent

settings = Settings.from_env()

# (label, href): pages get their own entry as they are written.
NAV = [
    ("Pipeline", "/pipeline"),
    ("Backtester", "/backtester"),
    ("Infrastructure", "/infrastructure"),
    ("Contact", "/#contact"),
]

# Every public page, for the sitemap. A test checks each one actually renders.
PAGES = ["/", "/pipeline", "/backtester", "/infrastructure", "/mentions-legales"]

# A public site, not an API: no /docs, /redoc or /openapi.json.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.filters.update(pct=pct, num=num, utc=utc, day=day)
templates.env.globals.update(settings=settings, nav=NAV)


def render(request: Request, template: str, page_path: str, **context: Any):
    return templates.TemplateResponse(
        request, template, {"page_path": page_path, **context}
    )


async def backtest_context() -> dict[str, Any]:
    backtest = await fetch_results(settings)
    return {"backtest": backtest, "chart": equity_chart(backtest.results["equity"])}


@app.get("/healthz")
async def healthz():
    # Liveness only: never depends on the backtester being reachable.
    return {"status": "ok"}


@app.get("/")
async def home(request: Request):
    return render(request, "home.html", "/", **await backtest_context())


@app.get("/backtester")
async def backtester(request: Request):
    return render(request, "backtester.html", "/backtester", **await backtest_context())


@app.get("/pipeline")
async def pipeline(request: Request):
    return render(request, "pipeline.html", "/pipeline")


@app.get("/infrastructure")
async def infrastructure(request: Request):
    return render(request, "infrastructure.html", "/infrastructure")


@app.get("/mentions-legales")
async def legal(request: Request):
    # In French regardless of the site language: LCEN notice for a site run from France.
    return render(request, "legal.html", "/mentions-legales")


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {settings.site_url}/sitemap.xml\n"


@app.get("/sitemap.xml")
async def sitemap():
    urls = "".join(f"  <url><loc>{settings.site_url}{path}</loc></url>\n" for path in PAGES)
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n"
    )
    return Response(body, media_type="application/xml")
