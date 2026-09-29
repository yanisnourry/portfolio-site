"""Server-side SVG helpers: charts are rendered in the HTML, no JS library."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EquityChart:
    points: str  # SVG ``points`` attribute, empty when there is nothing to draw
    lo: float | None = None
    hi: float | None = None
    baseline_y: float | None = None  # y of equity = 1.0 (starting capital), if in range


def equity_chart(
    equity: list[dict[str, Any]], width: float = 600, height: float = 120, pad: float = 4
) -> EquityChart:
    """Equity series -> polyline scaled to fit a ``width`` x ``height`` viewBox."""
    values = [p["equity"] for p in equity if p.get("equity") is not None]
    if len(values) < 2:
        return EquityChart(points="")
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0

    def y(v: float) -> float:
        return pad + (hi - v) / span * (height - 2 * pad)

    step = width / (len(values) - 1)
    points = " ".join(f"{i * step:.1f},{y(v):.1f}" for i, v in enumerate(values))
    baseline = round(y(1.0), 1) if lo <= 1.0 <= hi else None
    return EquityChart(points=points, lo=lo, hi=hi, baseline_y=baseline)
