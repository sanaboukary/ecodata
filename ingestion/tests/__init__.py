"""
Tests unitaires pour l'application Ingestion
"""
from django.test import TestCase, Client
from django.urls import reverse


class IngestionHealthTestCase(TestCase):
    """Tests pour l'endpoint de santé"""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_endpoint(self):
        """Test de l'endpoint health"""
        response = self.client.get(reverse('ingestion-health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertIn('status', data)


class IngestionStartTestCase(TestCase):
    """Tests pour le démarrage de l'ingestion"""
    
    def setUp(self):
        self.client = Client()
    
    def test_start_ingestion_post(self):
        """Test du démarrage de l'ingestion via POST"""
        response = self.client.post(
            reverse('ingestion-start'),
            content_type='application/json',
            data={'scripts_dir': './scripts'}
        )
        self.assertEqual(response.status_code, 200)
    
    def test_start_ingestion_get_not_allowed(self):
        """Test que GET n'est pas autorisé"""
        response = self.client.get(reverse('ingestion-start'))
        self.assertEqual(response.status_code, 405)
