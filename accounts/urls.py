from django.urls import path
from .views import RegisterAPIView, register, verify_email, jwt_login, logout_template, password_reset_request, password_reset_confirm, newsletter_subscribe, mailchimp_failed, mailchimp_confirm, contact, social_login
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'accounts'

urlpatterns = [
    path('api/register/', RegisterAPIView.as_view(), name='api_register'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', TokenRefreshView.as_view(), name='token_logout'),
    path('register/', register, name='register'),
    path('verify/', verify_email, name="verify_email"),
    path('login/', jwt_login, name='login'),
    path('logout/', logout_template, name='logout'),
    path('password-reset/', password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    path("newsletter/subscribe/", newsletter_subscribe, name="newsletter_subscribe"),
    path("newsletter/failed/", mailchimp_failed, name="mailchimp_failed"),
    path("newsletter/confirmed/", mailchimp_confirm, name="mailchimp_confirm"),
    path('contact', contact, name='contact'),
    path('social/', social_login, name='social_login'),
]