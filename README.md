# 👻 Ghost Employer Tracker Dashboard

A Python system that tracks job postings, detects repeated open/close patterns,
computes a **ghost score** for each employer, and displays everything on a static
dashboard hosted via **GitHub Pages**.

## Features

| Component | Details |
|-----------|---------|
| **Scraper** | `scraper/scraper.py` — `JobPosting` dataclass, `BaseScraper` interface, `MockScraper` with deterministic seeding |
| **Pattern Detector** | `scraper/pattern_detector.py` — ghost score (0–100) combining repost frequency, avg lifespan, and title vagueness |
| **Data Storage** | `data/jobs.json` — append-only JSON "database" (deduplicated by posting ID) |
| **Dashboard** | `docs/index.html` — dark-mode static page with Chart.js bar chart and per-company risk cards |
| **Automation** | `.github/workflows/update.yml` — daily GitHub Actions job that runs the scraper, re-generates `docs/data.json`, and commits back |

## Ghost Score

| Range | Risk | Meaning |
|-------|------|---------|
| 70–100 | 🔴 Critical | Strong ghost-employer signals |
| 50–69  | 🟠 High     | Multiple red flags |
| 30–49  | 🟡 Medium   | Worth monitoring |
| 0–29   | 🟢 Low      | Appears legitimate |

The score combines three heuristics (weighted out of 100):

1. **Repost frequency** (0–40 pts) — postings per company in the last 30 days.
2. **Short lifespan** (0–35 pts) — average days a listing stays open before closing.
3. **Title vagueness** (0–25 pts) — how generic the job title is (e.g. "Software Engineer" vs "Backend Engineer (Rust)").

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Generate data + dashboard
python generate_dashboard.py

# Preview the dashboard locally
python -m http.server 8000 --directory docs
# Open http://localhost:8000
```

## GitHub Pages Setup

1. Push this repository to GitHub.
2. Go to **Settings → Pages** and set the source to the `docs/` folder on the `main` branch.
3. The dashboard will be live at `https://<username>.github.io/<repo>/`.
4. The GitHub Actions workflow runs daily and commits fresh data automatically.

## Project Layout

```
ghost_hosts/
├── .github/workflows/update.yml   # Daily CI: scrape → analyse → commit
├── scraper/
│   ├── __init__.py
│   ├── scraper.py                 # JobPosting, BaseScraper, MockScraper
│   └── pattern_detector.py        # title_vagueness, compute_ghost_score, analyze_companies
├── tests/
│   ├── test_scraper.py
│   └── test_pattern_detector.py
├── docs/
│   ├── index.html                 # GitHub Pages dashboard
│   └── data.json                  # Generated company stats (auto-updated)
├── data/
│   └── jobs.json                  # Posting database (auto-updated)
├── generate_dashboard.py          # Orchestration script
├── requirements.txt
└── .gitignore
```
