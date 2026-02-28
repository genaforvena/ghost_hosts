"""Tests for scraper.scraper module."""

import json
import os
import tempfile
import unittest

from scraper.scraper import JobPosting, MockScraper


class TestJobPosting(unittest.TestCase):
    def test_to_dict_roundtrip(self):
        p = JobPosting(
            company="Acme",
            title="Engineer",
            posting_date="2024-01-01",
            status="open",
            url="https://example.com",
            source="mock",
            id="abc-123",
        )
        d = p.to_dict()
        self.assertEqual(d["company"], "Acme")
        self.assertEqual(d["title"], "Engineer")
        self.assertIsNone(d["close_date"])

    def test_from_dict(self):
        d = {
            "company": "Acme",
            "title": "Engineer",
            "posting_date": "2024-01-01",
            "status": "open",
            "url": "https://example.com",
            "source": "mock",
            "close_date": "2024-02-01",
            "id": "abc-123",
        }
        p = JobPosting.from_dict(d)
        self.assertEqual(p.company, "Acme")
        self.assertEqual(p.close_date, "2024-02-01")


class TestMockScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = MockScraper(seed=42, days_back=90)

    def test_scrape_returns_postings(self):
        postings = self.scraper.scrape()
        self.assertGreater(len(postings), 0)

    def test_scrape_all_fields_present(self):
        for p in self.scraper.scrape():
            self.assertTrue(p.id, "ID should be non-empty")
            self.assertTrue(p.company, "company should be non-empty")
            self.assertTrue(p.title, "title should be non-empty")
            self.assertTrue(p.posting_date, "posting_date should be non-empty")
            self.assertIn(p.status, ("open", "closed"))

    def test_scrape_deterministic(self):
        p1 = MockScraper(seed=99, days_back=90).scrape()
        p2 = MockScraper(seed=99, days_back=90).scrape()
        self.assertEqual(len(p1), len(p2))
        for a, b in zip(p1, p2):
            self.assertEqual(a.id, b.id)

    def test_save_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "jobs.json")
            postings = self.scraper.scrape()
            added1 = self.scraper.save(postings, path)
            self.assertEqual(added1, len(postings))
            # Second save with same data — no new rows.
            added2 = self.scraper.save(postings, path)
            self.assertEqual(added2, 0)

    def test_save_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "jobs.json")
            self.scraper.save(self.scraper.scrape(), path)
            with open(path) as fh:
                data = json.load(fh)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main()
