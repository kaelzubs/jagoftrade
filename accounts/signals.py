from allauth.socialaccount.signals import social_account_added, social_account_updated, pre_social_login
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(social_account_added)
def handle_social_account_added(request, sociallogin, **kwargs):
    user = sociallogin.user
    extra_data = sociallogin.account.extra_data
    # Optionally update user profile fields
    user.first_name = extra_data.get('first_name', user.first_name)
    user.last_name = extra_data.get('last_name', user.last_name)
    if not user.email:
        user.email = extra_data.get('email', user.email)
    user.save()

@receiver(social_account_updated)
def handle_social_account_updated(request, sociallogin, **kwargs):
    user = sociallogin.user
    extra_data = sociallogin.account.extra_data
    user.first_name = extra_data.get('first_name', user.first_name)
    user.last_name = extra_data.get('last_name', user.last_name)
    user.save()

@receiver(pre_social_login)
def handle_pre_social_login(request, sociallogin, **kwargs):
    # Optionally handle pre-login logic
    pass
