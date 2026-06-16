# myapp/tests.py
from django.test import TestCase
from .models import CustomUser

class CustomUserTests(TestCase):

    def test_create_user_successful(self):
        """Verify that create_user constructs a valid object with normalized attributes."""
        user = CustomUser.objects.create_user(
            email="candidate@test.com",
            name="Test Seeker",
            password="testpassword123"
        )
        self.assertEqual(user.email, "candidate@test.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        
        # Check that the default role falls back to CANDIDATE
        self.assertEqual(user.role, "CANDIDATE")
        
        # Verify that the automated signals attached a candidate profile profile row
        self.assertIsNotNone(user.candidate_profile)

    def test_create_user_missing_email_raises_error(self):
        """Verify that trying to build a profile without an email triggers a ValueError validation check."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(
                email="",
                name="No Email",
                password="password123"
            )