"""Runtime settings, read once from the environment."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # ClusterIP only: called server-side, never exposed to the browser.
    backtester_url: str = "http://backtester.backtester.svc.cluster.local:8000"
    # Short on purpose: a slow backtester must not hold the page.
    backtester_timeout_seconds: float = 2.0
    contact_email: str = "contact@yn-tech.fr"
    # Templates hide the links when set empty rather than ship a dead one.
    linkedin_url: str = "https://www.linkedin.com/in/yanis-nourry-profil/"
    github_url: str = "https://github.com/yanisnourry"
    # Canonical origin, used for OpenGraph and canonical URLs.
    site_url: str = "https://yn-tech.fr"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            backtester_url=os.getenv("BACKTESTER_URL", cls.backtester_url),
            backtester_timeout_seconds=float(
                os.getenv("BACKTESTER_TIMEOUT_SECONDS", cls.backtester_timeout_seconds)
            ),
            contact_email=os.getenv("CONTACT_EMAIL", cls.contact_email),
            linkedin_url=os.getenv("LINKEDIN_URL", cls.linkedin_url),
            github_url=os.getenv("GITHUB_URL", cls.github_url),
            site_url=os.getenv("SITE_URL", cls.site_url).rstrip("/"),
        )
