from django.test import TestCase, Client
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User


class ExplorerEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('dashboard.views.get_mongo_db')
    def test_autocomplete_indicators(self, mock_get_db):
        # Mock collection find returning indicator aliases
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.find.return_value = [{ 'indicator_alias': 'PIB_total_USD_courant' }, { 'indicator_alias': 'Inflation_CPI_annuelle_pct' }]
        mock_db.ext_worldbank_indicators = mock_collection
        mock_get_db.return_value = (None, mock_db)

        url = reverse('explorer-autocomplete-indicators')
        resp = self.client.get(url, { 'q': 'PIB' })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('items', data)
        self.assertTrue(any('PIB' in it for it in data['items']))

    @patch('dashboard.views.get_mongo_db')
    def test_autocomplete_countries(self, mock_get_db):
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.find.return_value = [{ 'country_name': 'Senegal' }, { 'country_name': 'Sierra Leone' }]
        mock_db.ext_worldbank_indicators = mock_collection
        mock_get_db.return_value = (None, mock_db)

        url = reverse('explorer-autocomplete-countries')
        resp = self.client.get(url, { 'q': 'Si' })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('items', data)
        self.assertTrue(any('Sierra' in it or 'Senegal' in it for it in data['items']))

    @patch('dashboard.views.get_mongo_db')
    def test_favorite_session_toggle(self, mock_get_db):
        # No DB needed for session fallback
        mock_get_db.return_value = (None, MagicMock())
        url = reverse('explorer-favorite')
        resp = self.client.post(url, { 'indicator_alias': 'PIB_total_USD_courant' })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('ok'))
        from django.test import TestCase, Client
        from django.urls import reverse
        from unittest.mock import patch, MagicMock
        from django.contrib.auth.models import User


        class ExplorerEndpointsTests(TestCase):
            def setUp(self):
                self.client = Client()

            @patch('dashboard.views.get_mongo_db')
            def test_autocomplete_indicators(self, mock_get_db):
                # Mock collection find returning indicator aliases
                mock_db = MagicMock()
                mock_collection = MagicMock()
                mock_collection.find.return_value = [
                    {'indicator_alias': 'PIB_total_USD_courant'},
                    {'indicator_alias': 'Inflation_CPI_annuelle_pct'},
                ]
                mock_db.ext_worldbank_indicators = mock_collection
                mock_get_db.return_value = (None, mock_db)

                url = reverse('explorer-autocomplete-indicators')
                resp = self.client.get(url, {'q': 'PIB'})
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertIn('items', data)
                self.assertTrue(
                    any('PIB' in it for it in data['items'])
                )

            @patch('dashboard.views.get_mongo_db')
            def test_autocomplete_countries(self, mock_get_db):
                mock_db = MagicMock()
                mock_collection = MagicMock()
                mock_collection.find.return_value = [
                    {'country_name': 'Senegal'},
                    {'country_name': 'Sierra Leone'},
                ]
                mock_db.ext_worldbank_indicators = mock_collection
                mock_get_db.return_value = (None, mock_db)

                url = reverse('explorer-autocomplete-countries')
                resp = self.client.get(url, {'q': 'Si'})
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertIn('items', data)
                self.assertTrue(
                    any('Sierra' in it or 'Senegal' in it for it in data['items'])
                )

            @patch('dashboard.views.get_mongo_db')
            def test_favorite_session_toggle(self, mock_get_db):
                # No DB needed for session fallback
                mock_get_db.return_value = (None, MagicMock())
                url = reverse('explorer-favorite')
                resp = self.client.post(url, {'indicator_alias': 'PIB_total_USD_courant'})
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertTrue(data.get('ok'))
                self.assertIn('favorites', data)
                # Toggling again should remove
                resp2 = self.client.post(url, {'indicator_alias': 'PIB_total_USD_courant'})
                self.assertEqual(resp2.status_code, 200)
                data2 = resp2.json()
                self.assertTrue(data2.get('ok'))

            @patch('dashboard.views.get_mongo_db')
            def test_favorite_persistent_for_authenticated(self, mock_get_db):
                # Setup mock db collections
                mock_db = MagicMock()
                user_fav_coll = MagicMock()
                # Initially find_one returns None -> will insert
                user_fav_coll.find_one.return_value = None
                user_fav_coll.find.return_value = []
                mock_db.user_favorites = user_fav_coll
                mock_get_db.return_value = (None, mock_db)

                # create and login user
                u = User.objects.create_user(username='tester', password='pwd')
                self.client.login(username='tester', password='pwd')

                url = reverse('explorer-favorite')
                resp = self.client.post(url, {'indicator_alias': 'PIB_total_USD_courant'})
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertTrue(data.get('ok'))
                # Ensure insert_one called
                self.assertTrue(mock_db.user_favorites.insert_one.called)

                # Simulate existing favorite now
                mock_db.user_favorites.find_one.return_value = {
                    '_id': 'abc', 'indicator_alias': 'PIB_total_USD_courant'
                }
                resp2 = self.client.post(url, {'indicator_alias': 'PIB_total_USD_courant'})
                self.assertEqual(resp2.status_code, 200)
                self.assertTrue(mock_db.user_favorites.delete_one.called)
