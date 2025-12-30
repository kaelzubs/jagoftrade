from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser # Replace with your model

class CustomUserAdmin(UserAdmin):
    # ... add your custom fieldsets here ...
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)