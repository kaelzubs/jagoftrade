from django.urls import path
from . import views

urlpatterns = [
    path("api/paapi/search", views.paapi_search, name="paapi_search"),
    path("api/paapi/items", views.paapi_get_items, name="paapi_get_items"),
]