"""Jinja filters for metrics and timestamps."""
from __future__ import annotations

from datetime import datetime


def pct(value: float | None, signed: bool = True) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:+.2f}%" if signed else f"{value * 100:.2f}%"


def num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def utc(value: str | None) -> str:
    if not value:
        return "n/a"
    return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M UTC")


def day(value: str | None) -> str:
    if not value:
        return "n/a"
    return datetime.fromisoformat(value).strftime("%Y-%m-%d")
