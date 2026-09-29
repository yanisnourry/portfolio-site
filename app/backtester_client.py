"""Server-side call to backtester-service ``/results``, with a static fallback.

The page never fails because of the backtester: any error (timeout, connection
refused, 503 before the first refresh, unexpected payload) degrades to a bundled
example, flagged ``live=False`` so the template labels it as such.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings

log = logging.getLogger(__name__)

FALLBACK_PATH = Path(__file__).resolve().parent / "fallback_results.json"
REQUIRED_KEYS = ("disclaimer", "computed_at", "strategy", "data", "metrics", "equity")


@dataclass(frozen=True)
class BacktestView:
    live: bool
    results: dict[str, Any]


def load_fallback() -> dict[str, Any]:
    return json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))


async def fetch_results(
    settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> BacktestView:
    try:
        async with httpx.AsyncClient(
            base_url=settings.backtester_url,
            timeout=settings.backtester_timeout_seconds,
            transport=transport,
        ) as client:
            resp = await client.get("/results")
        resp.raise_for_status()
        payload = resp.json()
        missing = [k for k in REQUIRED_KEYS if k not in payload]
        if missing:
            raise ValueError(f"missing keys in /results: {missing}")
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("backtester unavailable, serving static example: %r", exc)
        return BacktestView(live=False, results=load_fallback())
    return BacktestView(live=True, results=payload)
