"""Server-side SVG helpers: charts are rendered in the HTML, no JS library."""
from __future__ import annotations

from typing import Any


def sparkline_points(
    equity: list[dict[str, Any]], width: float = 600, height: float = 120, pad: float = 4
) -> str:
    """Equity series -> SVG ``points`` attribute, scaled to fit the viewBox."""
    values = [p["equity"] for p in equity if p.get("equity") is not None]
    if len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    step = width / (len(values) - 1)
    return " ".join(
        f"{i * step:.1f},{pad + (hi - v) / span * (height - 2 * pad):.1f}"
        for i, v in enumerate(values)
    )
