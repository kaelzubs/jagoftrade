from django.urls import path
from .views import home, cookie_settings, robots_txt

app_name = 'core'


urlpatterns = [
    path('', home, name='home'),
    path("cookies/", cookie_settings, name="cookie_settings"),
    path("robots.txt/", robots_txt, name="robots_txt"),
]