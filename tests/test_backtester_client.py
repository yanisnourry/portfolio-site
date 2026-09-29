import httpx

from app.backtester_client import fetch_results, load_fallback
from app.config import Settings

SETTINGS = Settings(backtester_url="http://backtester.test", backtester_timeout_seconds=0.5)


def live_payload() -> dict:
    payload = load_fallback()
    payload["computed_at"] = "2026-09-30T10:00:00+00:00"
    return payload


def transport(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


async def test_live_results():
    payload = live_payload()
    view = await fetch_results(SETTINGS, transport(lambda req: httpx.Response(200, json=payload)))
    assert view.live is True
    assert view.results == payload


async def test_calls_results_endpoint():
    seen = []

    def handler(req):
        seen.append(str(req.url))
        return httpx.Response(200, json=live_payload())

    await fetch_results(SETTINGS, transport(handler))
    assert seen == ["http://backtester.test/results"]


async def test_503_before_first_refresh_falls_back():
    body = {"detail": "no backtest result yet", "disclaimer": "..."}
    view = await fetch_results(SETTINGS, transport(lambda req: httpx.Response(503, json=body)))
    assert view.live is False
    assert view.results == load_fallback()


async def test_timeout_falls_back():
    def handler(req):
        raise httpx.ReadTimeout("timed out", request=req)

    view = await fetch_results(SETTINGS, transport(handler))
    assert view.live is False


async def test_connection_refused_falls_back():
    def handler(req):
        raise httpx.ConnectError("refused", request=req)

    view = await fetch_results(SETTINGS, transport(handler))
    assert view.live is False


async def test_non_json_falls_back():
    view = await fetch_results(SETTINGS, transport(lambda req: httpx.Response(200, text="<html>")))
    assert view.live is False


async def test_unexpected_payload_falls_back():
    view = await fetch_results(SETTINGS, transport(lambda req: httpx.Response(200, json={"foo": 1})))
    assert view.live is False


def test_fallback_has_contract_shape():
    fallback = load_fallback()
    for key in ("disclaimer", "computed_at", "strategy", "data", "metrics", "equity"):
        assert key in fallback
    assert "Not a trading signal" in fallback["disclaimer"]
