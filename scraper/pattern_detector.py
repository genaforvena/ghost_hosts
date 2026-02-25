"""Pattern detection and ghost-score calculation.

The "ghost score" (0–100) combines three heuristics:

* **Repost frequency** (up to 40 pts): how many postings appeared in the last
  30 days — repeated re-listings of the same role are a key red flag.
* **Short lifespan** (up to 35 pts): postings that open and close within days
  suggest the role was never real or filled externally.
* **Title vagueness** (up to 25 pts): broad titles like "Software Engineer"
  with no tech-stack specifics are more common in ghost postings.
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

_VAGUE_KEYWORDS = {
    "software engineer",
    "senior developer",
    "full stack",
    "developer",
    "project manager",
    "business analyst",
    "devops",
    "data scientist",
    "machine learning engineer",
    "product manager",
    "analyst",
    "engineer",
    "manager",
}

_SPECIFIC_PATTERN = re.compile(r"[\(\[/\+]")


def title_vagueness(title: str) -> float:
    """Return a vagueness score in [0.0, 1.0] for a job title.

    1.0 means extremely vague; 0.0 means highly specific.
    """
    lower = title.lower()
    matches = sum(1 for kw in _VAGUE_KEYWORDS if kw in lower)
    score = min(matches / 3.0, 1.0)
    if _SPECIFIC_PATTERN.search(title):
        score *= 0.4
    return round(score, 4)


def compute_ghost_score(postings: list) -> dict:
    """Compute ghost-score metrics for a list of postings from *one* company.

    Parameters
    ----------
    postings:
        List of posting dicts (as stored in ``data/jobs.json``).

    Returns
    -------
    dict with keys: ``ghost_score``, ``repost_count_30d``,
    ``repost_count_60d``, ``avg_lifespan_days``, ``title_vagueness``,
    ``total_postings``.
    """
    if not postings:
        return {
            "ghost_score": 0.0,
            "repost_count_30d": 0,
            "repost_count_60d": 0,
            "avg_lifespan_days": None,
            "title_vagueness": 0.0,
            "total_postings": 0,
        }

    now = datetime.now(timezone.utc).date()
    cutoff_30 = now - timedelta(days=30)
    cutoff_60 = now - timedelta(days=60)

    reposts_30d = 0
    reposts_60d = 0
    lifespans: list = []
    vagueness_scores: list = []

    for posting in postings:
        post_date = datetime.strptime(posting["posting_date"], "%Y-%m-%d").date()
        if post_date >= cutoff_30:
            reposts_30d += 1
        if post_date >= cutoff_60:
            reposts_60d += 1
        if posting.get("close_date"):
            close = datetime.strptime(posting["close_date"], "%Y-%m-%d").date()
            lifespans.append((close - post_date).days)
        vagueness_scores.append(title_vagueness(posting["title"]))

    avg_lifespan = sum(lifespans) / len(lifespans) if lifespans else None
    avg_vagueness = (
        sum(vagueness_scores) / len(vagueness_scores) if vagueness_scores else 0.0
    )

    # Ghost score components (0–100).
    # 1. Repost frequency (0–40 pts): each posting in last 30 days adds 5 pts.
    repost_score = min(reposts_30d * 5, 40)

    # 2. Short lifespan (0–35 pts): <7 days ≈ 35 pts, >60 days ≈ 0 pts.
    if avg_lifespan is not None:
        lifespan_score = max(0.0, 35.0 * (1 - avg_lifespan / 60.0))
    else:
        lifespan_score = 0.0

    # 3. Title vagueness (0–25 pts).
    vagueness_score = avg_vagueness * 25.0

    ghost_score = min(round(repost_score + lifespan_score + vagueness_score, 1), 100.0)

    return {
        "ghost_score": ghost_score,
        "repost_count_30d": reposts_30d,
        "repost_count_60d": reposts_60d,
        "avg_lifespan_days": round(avg_lifespan, 1) if avg_lifespan is not None else None,
        "title_vagueness": round(avg_vagueness, 4),
        "total_postings": len(postings),
    }


def analyze_companies(postings: list) -> list:
    """Group postings by company, compute ghost scores, return sorted list.

    Results are sorted by ``ghost_score`` descending (highest risk first).

    Each entry contains: ``company``, ``ghost_score``, ``repost_count_30d``,
    ``repost_count_60d``, ``avg_lifespan_days``, ``title_vagueness``,
    ``total_postings``, ``timeline`` (last 10 events, most recent first).
    """
    by_company: dict = defaultdict(list)
    for p in postings:
        by_company[p["company"]].append(p)

    results = []
    for company, company_postings in by_company.items():
        metrics = compute_ghost_score(company_postings)
        timeline = sorted(
            [
                {
                    "date": p["posting_date"],
                    "title": p["title"],
                    "status": p["status"],
                    "url": p["url"],
                }
                for p in company_postings
            ],
            key=lambda x: x["date"],
            reverse=True,
        )[:10]
        results.append({"company": company, **metrics, "timeline": timeline})

    return sorted(results, key=lambda x: x["ghost_score"], reverse=True)
