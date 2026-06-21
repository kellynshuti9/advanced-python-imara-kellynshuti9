"""
API endpoint tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class APITestCase(TestCase):
    """Test API endpoints"""

    def setUp(self):
        self.client = APIClient()
        
        # Create test users
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
        """Test successful login returns JWT token"""
        response = self.client.post('/api/token/', {
            'username': 'merchant',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_invalid_login_fails(self):
        """Test invalid login returns 401"""
        response = self.client.post('/api/token/', {
            'username': 'merchant',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_access_denied(self):
        """Test unauthenticated users get 401"""
        response = self.client.get('/api/merchants/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access_allowed(self):
        """Test authenticated users can access protected endpoints"""
        self.client.force_authenticate(user=self.merchant)
        response = self.client.get('/api/merchants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_merchant_can_access_own_profile(self):
        """Test merchant can access their own profile"""
        self.client.force_authenticate(user=self.merchant)
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'merchant')