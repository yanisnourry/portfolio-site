# Portfolio Site

Server-rendered portfolio site (FastAPI + Jinja2 + htmx) presenting the
projects that are actually built and running: the market data pipeline, the
vectorized backtester with its live demo, and the k3s infrastructure behind
them.

> Work in progress: pages are being written. This README describes the
> architecture that is in place.

## Architecture

```
browser  --HTTPS-->  Cloudflare Tunnel  -->  Traefik  -->  portfolio-site
                                                              |
                                           (server-side, cluster DNS, ClusterIP)
                                                              |
                                                   backtester-service /results
```

- **Everything is rendered server-side**, including the live backtest numbers.
  The browser never calls the backtester, and its internal URL never reaches
  the client.
- **Degraded mode.** The call to `/results` has a short timeout. On any failure
  (timeout, connection refused, `503` before the first refresh, unexpected
  payload) the page shows a bundled static example, clearly labelled as such,
  instead of an error.
- **No form, no database, no secret.** Contact is a `mailto:` link.

## Configuration

Environment variables, all optional:

| Variable | Default |
|---|---|
| `BACKTESTER_URL` | `http://backtester.backtester.svc.cluster.local:8000` |
| `BACKTESTER_TIMEOUT_SECONDS` | `2.0` |
| `CONTACT_EMAIL` | `contact@yn-tech.fr` |

## Run locally

Python 3.11+:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Without a reachable backtester the site runs in degraded mode. Tests (the
backtester is mocked, no network needed):

```bash
pytest
```
