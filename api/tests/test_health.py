"""
Health check tests
"""
from django.test import TestCase
from rest_framework.test import APIClient

class HealthCheckTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')

    def test_ready_endpoint(self):
        response = self.client.get('/ready/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('checks', data)

    def test_liveness_endpoint(self):
        response = self.client.get('/live/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'alive')