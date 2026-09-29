# Portfolio Site

Server-rendered portfolio site (FastAPI + Jinja2 + htmx) presenting the
projects that are actually built and running: the market data pipeline, the
vectorized backtester with its live demo, and the k3s infrastructure behind
them.

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
| `SITE_URL` | `https://yn-tech.fr` (canonical, OpenGraph, sitemap) |

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

## Pages

| Path | Content |
|---|---|
| `/` | Positioning, running projects, live backtest preview, services, contact |
| `/pipeline` | Market data pipeline: data flow, design decisions, API, production setup |
| `/backtester` | Live backtest (server-side) and how the engine stays honest |
| `/infrastructure` | Self-hosted k3s behind a Cloudflare Tunnel, security, delivery |
| `/mentions-legales` | Legal notice, in French (LCEN) |

Plus `/sitemap.xml`, `/robots.txt` and `/healthz` (liveness, never depends on
the backtester).

## Deployment

CI runs the tests, then builds the image and pushes it to
`ghcr.io/yanisnourry/portfolio-site` (tags `latest` and commit sha). It is
deployed on k3s from the separate `infra` repository, pinned by sha. The image
runs as a non-root user and supports a read-only root filesystem.

Asset URLs are root-relative on purpose: TLS ends at Cloudflare, so the app
only ever sees plain HTTP and an absolute `url_for()` link would come out as
`http://` on an `https` page.

