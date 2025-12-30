from django.urls import path
from .views import product_list, product_detail, search_product, category_list

app_name = 'catalog'

urlpatterns = [
    path('', product_list, name='list'),
    path('search-result/', search_product, name='search'),
    path('<slug:slug>/', product_detail, name='detail'),
    path("product/<slug:category_slug>/", product_list, name="product_list_by_category"),
    path("category/<slug:category_slug>/", category_list, name="category_list_by_category"),
]