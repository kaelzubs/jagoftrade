# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "autocomplete": "password",
            "class": "form-control",
            "placeholder": "Enter Password"
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "autocomplete": "confirm password",
            "class": "form-control",
            "placeholder": "Confirm Password"
        })
    )

    class Meta:
        model = CustomUser
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(attrs={
                "autocomplete": "username",
                "class": "form-control",
                "placeholder": "Enter Username"
            }),
            "email": forms.EmailInput(attrs={
                "autocomplete": "email",
                "class": "form-control",
                "placeholder": "Enter Email"
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
        
class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={
            "autocomplete": "username",
            "class": "form-control",
            "placeholder": "Enter Username or Email"
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "autocomplete": "password",
            "class": "form-control",
            "placeholder": "Enter Password"
        }
    ))
    
    
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        "autocomplete": "name",
        "class": "form-control", "placeholder": "Your Name"
        ""
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "autocomplete": "email",
        "class": "form-control", "placeholder": "Your Email"
    }))
    subject = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        "autocomplete": "subject",
        "class": "form-control", "placeholder": "Subject"
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        "autocomplete": "message",
        "class": "form-control", "placeholder": "Your Message", "rows": 5
    }))

