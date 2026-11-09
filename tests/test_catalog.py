"""Offline tests with synthetic catalog entries."""
import unittest
from star_template.catalog import Catalog, normalize_n8n, suggest_pairs
from star_template.n8n import N8nProvider, sync

def fixture(i, name, integrations):
    return normalize_n8n({"id": i, "name": name, "nodes": [
        {"name": n} for n in integrations], "categories": [{"name": "AI"}],
        "user": {"username": "creator"}})

class Tests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog(":memory:")
        self.catalog.upsert([
            fixture(1, "Slack to Sheets", ["Slack", "Google Sheets"]),
            fixture(2, "Slack alert", ["Slack", "OpenAI"]),
            fixture(3, "Sheets to Gmail", ["Google Sheets", "Gmail"])])

    def tearDown(self):
        self.catalog.conn.close()

    def test_search(self):
        self.assertEqual(len(self.catalog.search("Slack")), 2)
        self.assertEqual(len(self.catalog.search(integrations=["Google Sheets"])), 2)
        self.assertEqual(len(self.catalog.search("Slack", integrations=["Google Sheets"])), 1)
        self.assertEqual(len(self.catalog.search(exclude_integrations=["Slack"])), 1)
        self.assertEqual(len(self.catalog.search(category="AI")), 3)

    def test_upsert(self):
        self.catalog.upsert([fixture(1, "Updated", ["Slack"])])
        self.assertEqual(self.catalog.status()["total"], 3)
        self.assertEqual(self.catalog.get("n8n", "1")["title"], "Updated")
        self.assertEqual(self.catalog.search("Sheets", integrations=["Slack"]), [])

    def test_composition(self):
        result = suggest_pairs(self.catalog, "Slack")
        self.assertTrue(result["suggestions"])
        self.assertFalse(result["suggestions"][0]["compatibility_verified"])

    def test_url_and_namespaces(self):
        self.assertEqual(self.catalog.get("n8n", "1")["url"], "https://n8n.io/workflows/1")
        x = fixture(1, "Other source", ["Webhook"])
        x["source"] = "other"
        self.catalog.upsert([x])
        self.assertEqual(self.catalog.status()["total"], 4)
        self.assertEqual(len(self.catalog.search(source="other")), 1)

class ProviderTests(unittest.TestCase):
    def test_sync(self):
        class Fake:
            def fetch_page(self, page, rows):
                return ([fixture(10, "A", []), fixture(11, "B", [])], 3) if page == 1 \
                    else ([fixture(12, "C", [])], 3)
        with Catalog(":memory:") as db:
            result = sync(db, Fake(), pages=0, rows=2, delay=0)
            self.assertTrue(result["complete"])
            self.assertEqual(db.status()["total"], 3)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            normalize_n8n({"name": "No id"})
        with self.assertRaises(ValueError):
            N8nProvider("http://insecure.example")

if __name__ == "__main__":
    unittest.main()
