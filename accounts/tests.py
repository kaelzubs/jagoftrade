from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

User = get_user_model()

class SocialLoginIntegrationTest(TestCase):
    """Test social login functionality with Google and Facebook."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.register_url = reverse('accounts:register')
        self.social_login_url = reverse('accounts:social_login')
    
    def test_login_page_accessible(self):
        """Verify login page loads successfully."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
    
    def test_register_page_accessible(self):
        """Verify register page loads successfully."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Account')
    
    def test_social_login_page_exists(self):
        """Verify dedicated social login page is accessible."""
        response = self.client.get(self.social_login_url)
        self.assertEqual(response.status_code, 200)
    
    def test_social_login_page_displays_google_button(self):
        """Verify Google button on dedicated social login page."""
        response = self.client.get(self.social_login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue with Google')
        self.assertContains(response, 'fab fa-google')
    
    def test_social_login_page_displays_facebook_button(self):
        """Verify Facebook button on dedicated social login page."""
        response = self.client.get(self.social_login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue with Facebook')
        self.assertContains(response, 'fab fa-facebook-f')


class CustomSocialAccountAdapterTest(TestCase):
    """Test custom social account adapter for profile population."""
    
    def setUp(self):
        from accounts.adapters import CustomSocialAccountAdapter
        self.adapter = CustomSocialAccountAdapter()
    
    def test_populate_user_sets_first_name(self):
        """Verify adapter sets first_name from social provider data."""
        mock_request = MagicMock()
        mock_sociallogin = MagicMock()
        mock_sociallogin.account.extra_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        }
        
        user = self.adapter.populate_user(mock_request, mock_sociallogin, {})
        self.assertEqual(user.first_name, 'John')
    
    def test_populate_user_sets_last_name(self):
        """Verify adapter sets last_name from social provider data."""
        mock_request = MagicMock()
        mock_sociallogin = MagicMock()
        mock_sociallogin.account.extra_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        }
        
        user = self.adapter.populate_user(mock_request, mock_sociallogin, {})
        self.assertEqual(user.last_name, 'Doe')
    
    def test_populate_user_sets_email(self):
        """Verify adapter sets email from social provider data."""
        mock_request = MagicMock()
        mock_sociallogin = MagicMock()
        mock_sociallogin.account.extra_data = {
            'email': 'john@example.com'
        }
        
        user = self.adapter.populate_user(mock_request, mock_sociallogin, {})
        self.assertEqual(user.email, 'john@example.com')


class SocialAuthSignalsTest(TestCase):
    """Test signal handlers for social account operations."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_signals_module_imports(self):
        """Verify signals module can be imported."""
        try:
            import accounts.signals
            self.assertTrue(True)
        except ImportError:
            self.fail("accounts.signals module could not be imported")


class AllAuthConfigurationTest(TestCase):
    """Test django-allauth configuration."""
    
    def test_google_oauth_credentials_configured(self):
        """Verify Google OAuth credentials are configured."""
        from django.conf import settings
        google_settings = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        self.assertIsNotNone(google_settings, "Google OAuth should be configured")
        self.assertIn('SCOPE', google_settings)
    
    def test_facebook_oauth_credentials_configured(self):
        """Verify Facebook OAuth credentials are configured."""
        from django.conf import settings
        facebook_settings = settings.SOCIALACCOUNT_PROVIDERS.get('facebook', {})
        self.assertIsNotNone(facebook_settings, "Facebook OAuth should be configured")
        self.assertIn('SCOPE', facebook_settings)
    
    def test_socialaccount_auto_signup_enabled(self):
        """Verify auto signup is enabled for social accounts."""
        from django.conf import settings
        self.assertTrue(
            settings.SOCIALACCOUNT_AUTO_SIGNUP,
            "SOCIALACCOUNT_AUTO_SIGNUP should be enabled"
        )
    
    def test_custom_adapter_configured(self):
        """Verify custom social account adapter is configured."""
        from django.conf import settings
        self.assertEqual(
            settings.SOCIALACCOUNT_ADAPTER,
            'accounts.adapters.CustomSocialAccountAdapter',
            "Custom adapter should be configured"
        )

