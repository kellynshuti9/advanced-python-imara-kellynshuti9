"""
Health check tests
"""
from django.test import TestCase
from rest_framework.test import APIClient

class HealthCheckTest(TestCase):
    """Test health check endpoints"""

    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint(self):
        """Test /health/ endpoint"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('timestamp', data)

    def test_ready_endpoint(self):
        """Test /ready/ endpoint"""
        response = self.client.get('/ready/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('checks', data)
        self.assertIn('database', data['checks'])

    def test_liveness_endpoint(self):
        """Test /live/ endpoint"""
        response = self.client.get('/live/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'alive')