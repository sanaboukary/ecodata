"""
Tests unitaires pour l'application Dashboard
"""
from django.test import TestCase, Client
from django.urls import reverse


class DashboardViewsTestCase(TestCase):
    """Tests pour les vues du dashboard"""
    
    def setUp(self):
        self.client = Client()
    
    def test_index_view(self):
        """Test de la page d'accueil"""
        response = self.client.get(reverse('dashboard-index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
    
    def test_explorer_view(self):
        """Test de la page explorateur"""
        response = self.client.get(reverse('explorer'))
        self.assertEqual(response.status_code, 200)
    
    def test_comparateur_view(self):
        """Test de la page comparateur"""
        response = self.client.get(reverse('comparateur'))
        self.assertEqual(response.status_code, 200)


class KPIListTestCase(TestCase):
    """Tests pour l'API des KPIs"""
    
    def setUp(self):
        self.client = Client()
    
    def test_kpi_list_endpoint(self):
        """Test de l'endpoint KPI list"""
        response = self.client.get(reverse('kpi-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')


class ExplorerDataTestCase(TestCase):
    """Tests pour les données de l'explorateur"""
    
    def setUp(self):
        self.client = Client()
    
    def test_explorer_data_endpoint(self):
        """Test de l'endpoint explorer data"""
        response = self.client.get(reverse('explorer-data'))
        self.assertEqual(response.status_code, 200)
    
    def test_explorer_autocomplete_indicators(self):
        """Test de l'autocomplétion des indicateurs"""
        response = self.client.get(
            reverse('explorer-autocomplete-indicators'),
            {'q': 'GDP'}
        )
        self.assertEqual(response.status_code, 200)
    
    def test_explorer_autocomplete_countries(self):
        """Test de l'autocomplétion des pays"""
        response = self.client.get(
            reverse('explorer-autocomplete-countries'),
            {'q': 'Benin'}
        )
        self.assertEqual(response.status_code, 200)
