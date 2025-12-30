from django.urls import path
from . import views

app_name = "policies"

urlpatterns = [
    path("about/", views.about, name="about"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("affiliate/", views.affiliate, name="affiliate"),
    path("editorial/", views.editorial, name="editorial"),
    path("advertising/", views.advertising, name="advertising"),
    path("user-content/", views.user_content, name="user_content"),
    path("accessibility/", views.accessibility, name="accessibility"),
    path("faqs/", views.faqs, name="faqs"),
]