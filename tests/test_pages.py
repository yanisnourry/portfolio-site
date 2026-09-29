import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.backtester_client import BacktestView, load_fallback
from app.charts import equity_chart

client = TestClient(main.app)


def live_view(**overrides) -> BacktestView:
    results = load_fallback()
    results.update(computed_at="2026-09-30T10:00:03+00:00", **overrides)
    return BacktestView(live=True, results=results)


@pytest.fixture
def backtest(monkeypatch):
    """Replace the backtester call; tests set ``backtest.view``."""

    class Stub:
        view = live_view()

    async def fake_fetch(settings):
        return Stub.view

    monkeypatch.setattr(main, "fetch_results", fake_fetch)
    return Stub


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_docs_disabled():
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404


def test_home_live(backtest):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "Computed 2026-09-30 10:00 UTC" in html
    assert "Live service temporarily unavailable" not in html
    assert "Not a trading signal" in html
    assert "<polyline" in html


def test_home_degraded(backtest):
    backtest.view = BacktestView(live=False, results=load_fallback())
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Live service temporarily unavailable" in resp.text
    assert "Not a trading signal" in resp.text


def test_home_stale(backtest):
    backtest.view = live_view(stale=True)
    html = client.get("/").text
    assert "Live · delayed" in html
    assert "Last successful refresh 2026-09-30 10:00 UTC" in html


def test_home_null_metric(backtest):
    view = live_view()
    view.results["metrics"]["sharpe_ratio"] = None
    backtest.view = view
    assert "n/a" in client.get("/").text


def test_home_real_degraded_path(monkeypatch):
    """No stub: an unreachable backtester still renders the page."""
    monkeypatch.setattr(
        main,
        "settings",
        main.Settings(backtester_url="http://127.0.0.1:9", backtester_timeout_seconds=0.5),
    )
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Live service temporarily unavailable" in resp.text


def test_home_never_leaks_internal_url(backtest):
    for view in (live_view(), BacktestView(live=False, results=load_fallback())):
        backtest.view = view
        assert "svc.cluster.local" not in client.get("/").text


def test_home_contact_and_meta(backtest):
    html = client.get("/").text
    assert 'href="mailto:contact@yn-tech.fr"' in html
    assert '<meta property="og:title"' in html
    assert '<link rel="canonical" href="https://yn-tech.fr/">' in html


def test_static_assets():
    assert client.get("/static/css/site.css").status_code == 200
    assert client.get("/static/favicon.svg").status_code == 200


def test_backtester_page_live(backtest):
    resp = client.get("/backtester")
    assert resp.status_code == 200
    html = resp.text
    assert "Simulation, not a trading signal." in html
    assert "Computed 2026-09-30 10:00 UTC" in html
    assert "Profit factor" in html
    assert 'class="baseline"' in html
    assert 'href="/backtester" aria-current="page"' in html


def test_backtester_page_degraded(backtest):
    backtest.view = BacktestView(live=False, results=load_fallback())
    resp = client.get("/backtester")
    assert resp.status_code == 200
    assert "Live service temporarily unavailable" in resp.text


def test_backtester_page_never_leaks_internal_url(backtest):
    assert "svc.cluster.local" not in client.get("/backtester").text


def test_pipeline_page():
    resp = client.get("/pipeline")
    assert resp.status_code == 200
    html = resp.text
    assert 'href="/pipeline" aria-current="page"' in html
    assert "https://api.yn-tech.fr/docs" in html
    assert "/static/img/pipeline-dashboard.jpg" in html
    assert client.get("/static/img/pipeline-dashboard.jpg").status_code == 200


def test_pipeline_page_does_not_call_backtester(monkeypatch):
    async def boom(settings):
        raise AssertionError("the pipeline page must not call the backtester")

    monkeypatch.setattr(main, "fetch_results", boom)
    assert client.get("/pipeline").status_code == 200


def test_infrastructure_page():
    resp = client.get("/infrastructure")
    assert resp.status_code == 200
    assert 'href="/infrastructure" aria-current="page"' in resp.text
    assert "https://github.com/yanisnourry/infra" in resp.text


def test_infrastructure_page_never_claims_dnssec():
    """DNSSEC is not enabled on the zone (no DS record in .fr): never claim it."""
    assert "dnssec" not in client.get("/infrastructure").text.lower()


def test_no_season_naming(backtest):
    """Internal roadmap vocabulary never reaches public pages."""
    for path in ("/", "/backtester", "/pipeline", "/infrastructure"):
        html = client.get(path).text.lower()
        assert "season" not in html and "saison" not in html


def test_equity_chart_scales_to_viewbox():
    chart = equity_chart([{"equity": 1.0}, {"equity": 2.0}, {"equity": 1.5}], 100, 50, pad=0)
    assert chart.points == "0.0,50.0 50.0,0.0 100.0,25.0"
    assert (chart.lo, chart.hi) == (1.0, 2.0)
    assert chart.baseline_y == 50.0


def test_equity_chart_baseline_out_of_range():
    chart = equity_chart([{"equity": 1.1}, {"equity": 1.2}])
    assert chart.baseline_y is None


def test_equity_chart_needs_two_points():
    assert equity_chart([{"equity": 1.0}]).points == ""
