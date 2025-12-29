from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch


class DashboardIndexViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _make_dummy_db(self):
        class DummyCursor(list):
            def sort(self, *a, **k):
                return self

            def limit(self, *a, **k):
                return self

            def skip(self, *a, **k):
                return self

        class DummyColl:
            def find(self, *a, **k):
                return DummyCursor([])

            def aggregate(self, *a, **k):
                return []

            def find_one(self, *a, **k):
                return None

            def count_documents(self, *a, **k):
                return 0

        class DummyDB:
            kpi_snapshots = DummyColl()
            ingestion_runs = DummyColl()
            ext_worldbank_indicators = DummyColl()

        return DummyDB()

    @patch('dashboard.views.get_mongo_db')
    def test_index_renders(self, mock_get_db):
        # Provide a dummy DB object so the view does not attempt real DB access
        mock_get_db.return_value = (None, self._make_dummy_db())
        url = reverse('dashboard-index')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Ensure the expected template is used
        templates = [t.name for t in resp.templates if t.name]
        self.assertIn('dashboard/index.html', templates)

    @patch('dashboard.views.get_mongo_db')
    def test_includes_dashboard_js(self, mock_get_db):
        """Vérifie que le template inclut le script static
        `js/dashboard_index.js`."""
        mock_get_db.return_value = (None, self._make_dummy_db())
        url = reverse('dashboard-index')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        # The template should include the static path to our JS
        self.assertIn("js/dashboard_index.js", content)
