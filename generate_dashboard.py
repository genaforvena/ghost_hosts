#!/usr/bin/env python3
"""Main orchestration script.

Usage
-----
    python generate_dashboard.py

Steps
-----
1. Run the MockScraper to generate / refresh job posting data.
2. Save new postings to ``data/jobs.json`` (JSON "database").
3. Load all postings, compute ghost scores per company.
4. Write ``docs/data.json`` for the static dashboard to consume.
"""

import json
import os
import sys
from datetime import datetime, timezone

from scraper.pattern_detector import analyze_companies
from scraper.scraper import MockScraper

DATA_FILE = "data/jobs.json"
DOCS_DIR = "docs"
DATA_JSON = os.path.join(DOCS_DIR, "data.json")


def load_postings(path: str = DATA_FILE) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return json.load(fh)


def main() -> int:
    # 1. Scrape (mock) postings — use a fresh seed each run so data varies.
    scraper = MockScraper(seed=None)
    new_postings = scraper.scrape()
    added = scraper.save(new_postings, DATA_FILE)
    print(f"Added {added} new postings  (total candidates: {len(new_postings)})")

    # 2. Load full dataset.
    all_postings = load_postings()
    print(f"Total postings in database : {len(all_postings)}")

    # 3. Analyse.
    company_stats = analyze_companies(all_postings)
    print(f"Companies analysed         : {len(company_stats)}")

    # 4. Write dashboard data.
    os.makedirs(DOCS_DIR, exist_ok=True)
    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_postings": len(all_postings),
        "companies": company_stats,
    }
    with open(DATA_JSON, "w") as fh:
        json.dump(output, fh, indent=2)
    print(f"Dashboard data written to  : {DATA_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
