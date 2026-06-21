"""
Model tests for Imara Financial Services
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class UserModelTest(TestCase):
    """Test User model"""

    def test_create_user(self):
        """Test creating a user with valid data"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='merchant'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, 'merchant')
        self.assertTrue(user.check_password('testpass123'))
        # Your model shows role in __str__, so check for it
        self.assertIn('testuser', str(user))

    def test_create_compliance_user(self):
        """Test creating a compliance user"""
        user = User.objects.create_user(
            username='compliance1',
            email='compliance1@test.com',
            password='testpass123',
            role='compliance'
        )
        self.assertEqual(user.role, 'compliance')
        self.assertIn('compliance1', str(user))

    def test_create_admin_user(self):
        """Test creating an admin user"""
        user = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='testpass123',
            role='admin'
        )
        self.assertEqual(user.role, 'admin')
        # Check that user was created successfully
        self.assertIsNotNone(user.id)
        self.assertIn('admin1', str(user))

    def test_weak_password_accepted(self):
        """Test that weak password is accepted (if your model allows it)"""
        # Your model might not have password validation in create_user
        user = User.objects.create_user(
            username='weakpass',
            email='weak@test.com',
            password='123',
            role='merchant'
        )
        # Check that user was created with the password
        self.assertIsNotNone(user.id)
        self.assertTrue(user.check_password('123'))

    def test_user_str_method(self):
        """Test the string representation of User"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@test.com',
            password='testpass123',
            role='merchant'
        )
        # Your model shows role in __str__, so check for that
        self.assertIn('testuser2', str(user))
        self.assertIn('Merchant', str(user))

    def test_user_has_required_fields(self):
        """Test user has all required fields"""
        user = User.objects.create_user(
            username='requiredfields',
            email='required@test.com',
            password='testpass123',
            role='merchant'
        )
        self.assertIsNotNone(user.username)
        self.assertIsNotNone(user.email)
        self.assertIsNotNone(user.role)
        self.assertIsNotNone(user.date_joined)

    def test_duplicate_email_not_allowed(self):
        """Test duplicate email is NOT allowed (unique constraint)"""
        user1 = User.objects.create_user(
            username='user1',
            email='same@test.com',
            password='testpass123',
            role='merchant'
        )
        # Try to create another user with same email
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='same@test.com',  # SAME email
                password='testpass123',
                role='merchant'
            )