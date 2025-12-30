from django.urls import path
from .views import cart_detail, cart_add, cart_remove, checkout, order_success, verify_paystack, calculate_shipping_api, update_cart_qty

app_name = 'orders'

urlpatterns = [
    path('cart/', cart_detail, name='cart_detail'),
    path('checkout/', checkout, name='checkout'),
    path('cart/add/<int:product_id>/', cart_add, name='cart_add'),
    path('success/<int:order_id>/', order_success, name='success'),
    path('paystack/verify/', verify_paystack, name='verify_paystack'),
    path('cart/remove/<int:product_id>/', cart_remove, name='cart_remove'),
    path('api/calculate-shipping/', calculate_shipping_api, name='calculate_shipping_api'),
    path('api/update-cart-qty/', update_cart_qty, name='update_cart_qty'),
]