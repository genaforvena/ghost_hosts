"""Job posting scraper module.

Provides a base class for scrapers and a MockScraper that generates
realistic sample data for demonstration and testing.
"""

import json
import os
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

# Companies that exhibit ghost-employer behaviour (many reposts, vague titles)
_GHOST_COMPANIES = [
    "TechVentures Inc.",
    "Global Solutions Ltd.",
    "Innovation Corp",
    "Digital Dynamics",
    "Future Systems",
]

# Normal companies (few postings, specific titles, longer lifespans)
_NORMAL_COMPANIES = [
    "Acme Software",
    "DataBridge Co.",
    "CloudStack Inc.",
    "OpenSource LLC",
]

_VAGUE_TITLES = [
    "Software Engineer",
    "Senior Developer",
    "Full Stack Developer",
    "Project Manager",
    "Business Analyst",
    "DevOps Engineer",
    "Data Scientist",
    "Machine Learning Engineer",
]

_SPECIFIC_TITLES = [
    "iOS Engineer (Swift/SwiftUI)",
    "Backend Engineer (Rust)",
    "Data Engineer (dbt + Snowflake)",
    "Site Reliability Engineer (Kubernetes)",
    "Security Engineer (Zero-Trust, IAM)",
]


@dataclass
class JobPosting:
    """Represents a single job posting."""

    company: str
    title: str
    posting_date: str          # ISO-8601 date string, e.g. "2024-01-15"
    status: str                # "open" or "closed"
    url: str
    source: str
    close_date: Optional[str] = None   # ISO-8601 date string or None
    id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "JobPosting":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class BaseScraper:
    """Abstract base class for job scrapers."""

    def scrape(self) -> list:
        """Return a list of JobPosting objects."""
        raise NotImplementedError

    def save(self, postings: list, path: str = "data/jobs.json") -> int:
        """Append new (non-duplicate) postings to the JSON database.

        Returns the number of newly added postings.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing: list = []
        if os.path.exists(path):
            with open(path) as fh:
                existing = json.load(fh)

        existing_ids = {p.get("id") for p in existing}
        new = [p.to_dict() for p in postings if p.id not in existing_ids]

        with open(path, "w") as fh:
            json.dump(existing + new, fh, indent=2)

        return len(new)


class MockScraper(BaseScraper):
    """Generates realistic sample data for demonstration and testing.

    Parameters
    ----------
    seed:
        Random seed for reproducible output.  Pass ``None`` for random results.
    days_back:
        How many days into the past to spread the generated postings.
    """

    def __init__(self, seed: Optional[int] = 42, days_back: int = 90):
        self._rng = random.Random(seed)
        self.days_back = days_back

    def scrape(self) -> list:
        postings: list = []
        now = datetime.now(timezone.utc)

        # Ghost employers — many reposts of vague titles, short lifespans
        for company in _GHOST_COMPANIES:
            num = self._rng.randint(5, 10)
            for i in range(num):
                title = self._rng.choice(_VAGUE_TITLES)
                offset = self._rng.randint(0, self.days_back)
                post_date = now - timedelta(days=offset)
                lifespan = self._rng.randint(3, 14)
                close_date = post_date + timedelta(days=lifespan)
                status = "closed" if close_date < now else "open"
                pid = (
                    f"{company}-{title}-{post_date.date()}-{i}".replace(" ", "_")
                )
                postings.append(
                    JobPosting(
                        company=company,
                        title=title,
                        posting_date=post_date.strftime("%Y-%m-%d"),
                        status=status,
                        url=f"https://example.com/jobs/{pid}",
                        source="mock",
                        close_date=close_date.strftime("%Y-%m-%d")
                        if status == "closed"
                        else None,
                        id=pid,
                    )
                )

        # Normal employers — few postings of specific titles, longer lifespans
        for company in _NORMAL_COMPANIES:
            num = self._rng.randint(1, 3)
            for i in range(num):
                title = self._rng.choice(_SPECIFIC_TITLES)
                offset = self._rng.randint(0, self.days_back)
                post_date = now - timedelta(days=offset)
                lifespan = self._rng.randint(30, 60)
                close_date = post_date + timedelta(days=lifespan)
                status = "closed" if close_date < now else "open"
                pid = (
                    f"{company}-{title}-{post_date.date()}-{i}".replace(" ", "_")
                )
                postings.append(
                    JobPosting(
                        company=company,
                        title=title,
                        posting_date=post_date.strftime("%Y-%m-%d"),
                        status=status,
                        url=f"https://example.com/jobs/{pid}",
                        source="mock",
                        close_date=close_date.strftime("%Y-%m-%d")
                        if status == "closed"
                        else None,
                        id=pid,
                    )
                )

        return postings
