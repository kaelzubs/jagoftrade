from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Ensure first_name and last_name are set from provider data
        extra_data = sociallogin.account.extra_data
        user.first_name = extra_data.get('first_name', user.first_name)
        user.last_name = extra_data.get('last_name', user.last_name)
        if not user.email:
            user.email = extra_data.get('email', '')
        return user
