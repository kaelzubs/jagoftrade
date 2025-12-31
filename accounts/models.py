from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Override email field to enforce uniqueness
    email = models.EmailField(unique=True)

    # Make email the primary identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # still keep username for display if you want

    def __str__(self):
        # Represent the user by email instead of username
        return self.email
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
