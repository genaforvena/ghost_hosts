"""Tests for scraper.pattern_detector module."""

import unittest

from scraper.pattern_detector import (
    analyze_companies,
    compute_ghost_score,
    title_vagueness,
)
from scraper.scraper import MockScraper


class TestTitleVagueness(unittest.TestCase):
    def test_score_in_range(self):
        for title in ["Software Engineer", "iOS Engineer (Swift/SwiftUI)", ""]:
            score = title_vagueness(title)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_vague_titles_score_high(self):
        for title in ["Software Engineer", "Senior Developer", "Machine Learning Engineer"]:
            self.assertGreater(title_vagueness(title), 0.5, f"{title!r} should be vague")

    def test_specific_titles_score_low(self):
        for title in [
            "iOS Engineer (Swift/SwiftUI)",
            "Backend Engineer (Rust)",
            "Data Engineer (dbt + Snowflake)",
        ]:
            self.assertLessEqual(title_vagueness(title), 0.5, f"{title!r} should be specific")


class TestComputeGhostScore(unittest.TestCase):
    def test_empty_returns_zeros(self):
        result = compute_ghost_score([])
        self.assertEqual(result["ghost_score"], 0.0)
        self.assertEqual(result["repost_count_30d"], 0)
        self.assertIsNone(result["avg_lifespan_days"])

    def test_score_in_range(self):
        postings = [p.to_dict() for p in MockScraper(seed=42).scrape()]
        by_company: dict = {}
        for p in postings:
            by_company.setdefault(p["company"], []).append(p)
        for company, cp in by_company.items():
            score = compute_ghost_score(cp)["ghost_score"]
            self.assertGreaterEqual(score, 0.0, company)
            self.assertLessEqual(score, 100.0, company)

    def test_total_postings_matches(self):
        postings = [p.to_dict() for p in MockScraper(seed=42).scrape()]
        by_company: dict = {}
        for p in postings:
            by_company.setdefault(p["company"], []).append(p)
        for company, cp in by_company.items():
            result = compute_ghost_score(cp)
            self.assertEqual(result["total_postings"], len(cp), company)


class TestAnalyzeCompanies(unittest.TestCase):
    def setUp(self):
        raw = MockScraper(seed=42).scrape()
        self.postings = [p.to_dict() for p in raw]

    def test_returns_all_companies(self):
        results = analyze_companies(self.postings)
        companies = {r["company"] for r in results}
        self.assertIn("TechVentures Inc.", companies)
        self.assertIn("Acme Software", companies)

    def test_sorted_descending(self):
        results = analyze_companies(self.postings)
        scores = [r["ghost_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_timeline_capped_at_ten(self):
        results = analyze_companies(self.postings)
        for r in results:
            self.assertLessEqual(len(r["timeline"]), 10, r["company"])
            self.assertGreater(len(r["timeline"]), 0, r["company"])

    def test_ghost_companies_outscore_normal(self):
        ghost_set = {
            "TechVentures Inc.",
            "Global Solutions Ltd.",
            "Innovation Corp",
            "Digital Dynamics",
            "Future Systems",
        }
        results = analyze_companies(self.postings)
        ghost_scores = [r["ghost_score"] for r in results if r["company"] in ghost_set]
        normal_scores = [r["ghost_score"] for r in results if r["company"] not in ghost_set]
        self.assertGreater(
            sum(ghost_scores) / len(ghost_scores),
            sum(normal_scores) / len(normal_scores),
        )


if __name__ == "__main__":
    unittest.main()
