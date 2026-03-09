"""
Script de test du Data Marketplace
Vérifie que toutes les fonctionnalités fonctionnent correctement
"""
from django.test import TestCase, Client
from django.urls import reverse
import json


class DataMarketplaceTest(TestCase):
    """Tests du marketplace de données"""
    
    def setUp(self):
        """Initialisation"""
        self.client = Client()
        
    def test_marketplace_page_loads(self):
        """Test 1: La page marketplace se charge"""
        response = self.client.get('/dashboard/marketplace/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marketplace de Données')
        print("✅ Test 1: Page marketplace chargée")
        
    def test_stats_displayed(self):
        """Test 2: Les statistiques s'affichent"""
        response = self.client.get('/dashboard/marketplace/')
        self.assertContains(response, 'Observations')
        self.assertContains(response, 'Actions BRVM')
        print("✅ Test 2: Statistiques affichées")
        
    def test_prepare_download(self):
        """Test 3: Préparation téléchargement"""
        response = self.client.post(
            '/dashboard/marketplace/prepare/',
            data=json.dumps({
                'source': 'BRVM',
                'period': '7d',
                'format': 'csv'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('count', data)
        self.assertIn('preview', data)
        print(f"✅ Test 3: Préparation OK - {data['count']} observations")
        
    def test_download_csv(self):
        """Test 4: Téléchargement CSV"""
        response = self.client.get(
            '/dashboard/marketplace/download/',
            {
                'source': 'BRVM',
                'period': '7d',
                'format': 'csv'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8-sig')
        self.assertIn('attachment', response['Content-Disposition'])
        print("✅ Test 4: Téléchargement CSV réussi")
        
    def test_download_json(self):
        """Test 5: Téléchargement JSON"""
        response = self.client.get(
            '/dashboard/marketplace/download/',
            {
                'source': 'BRVM',
                'period': '7d',
                'format': 'json'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        print("✅ Test 5: Téléchargement JSON réussi")
        
    def test_api_documentation(self):
        """Test 6: Documentation API"""
        response = self.client.get('/dashboard/marketplace/api-docs/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('endpoints', data)
        self.assertIn('code_examples', data)
        print(f"✅ Test 6: Documentation API - {len(data['endpoints'])} endpoints")
        
    def test_all_sources(self):
        """Test 7: Toutes les sources disponibles"""
        sources = ['BRVM', 'WorldBank', 'IMF', 'UN_SDG', 'AfDB', 'BRVM_PUBLICATION']
        
        for source in sources:
            response = self.client.post(
                '/dashboard/marketplace/prepare/',
                data=json.dumps({
                    'source': source,
                    'period': '7d',
                    'format': 'csv'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            print(f"   ✓ {source}: {data.get('count', 0)} observations")
        
        print("✅ Test 7: Toutes les sources fonctionnelles")
        
    def test_all_periods(self):
        """Test 8: Toutes les périodes"""
        periods = ['7d', '30d', '60d', '1y', 'all']
        
        for period in periods:
            response = self.client.post(
                '/dashboard/marketplace/prepare/',
                data=json.dumps({
                    'source': 'BRVM',
                    'period': period,
                    'format': 'csv'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            print(f"   ✓ {period}: {data.get('count', 0)} observations")
        
        print("✅ Test 8: Toutes les périodes fonctionnelles")


def run_manual_tests():
    """
    Tests manuels (sans Django TestCase)
    Exécutez avec: python test_marketplace.py
    """
    import requests
    
    BASE_URL = 'http://localhost:8000/dashboard/marketplace'
    
    print("\n" + "="*60)
    print("🧪 TESTS MARKETPLACE - Exécution manuelle")
    print("="*60 + "\n")
    
    # Test 1: Page principale
    print("Test 1: Chargement page marketplace...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert 'Marketplace de Données' in response.text
        print("✅ PASS: Page chargée correctement\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
    
    # Test 2: Préparation téléchargement
    print("Test 2: Préparation téléchargement BRVM...")
    try:
        response = requests.post(
            f"{BASE_URL}/prepare/",
            json={
                'source': 'BRVM',
                'period': '60d',
                'format': 'csv'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        print(f"✅ PASS: {data['count']} observations trouvées")
        print(f"   Taille estimée: {data['estimated_size']}\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
    
    # Test 3: Téléchargement CSV
    print("Test 3: Téléchargement CSV...")
    try:
        response = requests.get(
            f"{BASE_URL}/download/",
            params={
                'source': 'BRVM',
                'period': '7d',
                'format': 'csv'
            }
        )
        assert response.status_code == 200
        assert 'text/csv' in response.headers['Content-Type']
        
        # Sauvegarder fichier test
        with open('test_brvm.csv', 'wb') as f:
            f.write(response.content)
        
        print("✅ PASS: Fichier CSV téléchargé → test_brvm.csv\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
    
    # Test 4: Téléchargement JSON
    print("Test 4: Téléchargement JSON...")
    try:
        response = requests.get(
            f"{BASE_URL}/download/",
            params={
                'source': 'WorldBank',
                'period': '30d',
                'format': 'json'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        print(f"✅ PASS: {len(data)} observations JSON\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
    
    # Test 5: Documentation API
    print("Test 5: Documentation API...")
    try:
        response = requests.get(f"{BASE_URL}/api-docs/")
        assert response.status_code == 200
        docs = response.json()
        assert 'endpoints' in docs
        assert 'code_examples' in docs
        
        print(f"✅ PASS: {len(docs['endpoints'])} endpoints documentés")
        print(f"   Exemples: Python, JavaScript, R\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
    
    # Test 6: Performance
    print("Test 6: Test de performance (100 requêtes)...")
    try:
        import time
        start = time.time()
        
        for i in range(100):
            requests.post(
                f"{BASE_URL}/prepare/",
                json={
                    'source': 'BRVM',
                    'period': '7d',
                    'format': 'csv'
                }
            )
        
        duration = time.time() - start
        avg = duration / 100 * 1000
        
        print(f"✅ PASS: Temps moyen {avg:.2f}ms par requête")
        print(f"   Total 100 requêtes: {duration:.2f}s\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
    
    print("="*60)
    print("✨ Tests terminés!")
    print("="*60)


if __name__ == '__main__':
    """
    Exécution directe: python test_marketplace.py
    Avec Django: python manage.py test dashboard.test_marketplace
    """
    run_manual_tests()
