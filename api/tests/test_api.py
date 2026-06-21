"""
API tests for Imara Financial Services
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.merchant = User.objects.create_user(
            username='merchant',
            email='merchant@test.com',
            password='testpass123',
            role='merchant'
        )
        self.compliance = User.objects.create_user(
            username='compliance',
            email='compliance@test.com',
            password='testpass123',
            role='compliance'
        )

    def test_login_returns_token(self):
        response = self.client.post('/api/token/', {
            'username': 'merchant',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_invalid_login_fails(self):
        response = self.client.post('/api/token/', {
            'username': 'merchant',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_access_denied(self):
        response = self.client.get('/api/merchants/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access_allowed(self):
        self.client.force_authenticate(user=self.merchant)
        response = self.client.get('/api/merchants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_merchant_can_access_own_profile(self):
        self.client.force_authenticate(user=self.merchant)
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)