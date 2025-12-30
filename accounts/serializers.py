from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {'password': {'write_only': True}}
    
    # In your serializer's create method or view's form handling
    def create(self, validated_data):
        password2 = validated_data.pop('password2', None) # Remove password2
        # ... perform password comparison/validation here if not done in validate()
        user = User.objects.create_user(**validated_data)
        return user
