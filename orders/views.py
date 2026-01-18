from itertools import product
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem, Address
from catalog.models import Product
from .emails import send_order_confirmation_email
from django.conf import settings
from pathlib import Path
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from shop.payments.paystack import initialize_transaction, verify_transaction
from orders.shipping import get_all_shipping_options
from decimal import Decimal
from django.contrib.auth.decorators import login_required

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

@login_required
def cart_detail(request):
    cart = Cart(request)
    # Get shipping options to show on cart page
    items = list(cart.items())
    shipping_options = get_all_shipping_options(items, destination_state=None, cart_subtotal=Decimal('0'))
    
    # Calculate items count and item value
    items_count = sum(item['quantity'] for item in items)
    item_value = sum(item['line_total'] for item in items)
    
    return render(request, 'orders/cart.html', {
        'cart_items': items,
        'totals': cart.totals(),
        "cart_count": len(cart),
        "cart": cart,
        'shipping_options': shipping_options,
        'items_count': items_count,
        'item_value': item_value,
    })

@login_required
def cart_add(request, product_id):
    cart = Cart(request)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        # ✅ Fetch the actual product object
        # ✅ Pass the product object, not just the ID
        product = get_object_or_404(Product, id=product_id)
        if str(product.id) not in cart.cart:
            cart.add(product_id, qty)
            
    return redirect('orders:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return redirect('orders:cart_detail')

def checkout(request):
    cart = Cart(request)
    items = list(cart.items())
    
    # Get shipping method from POST or default to 'standard'
    shipping_method = request.POST.get('shipping_method', 'standard') if request.method == 'POST' else 'standard'
    destination_state = request.POST.get('state', None) if request.method == 'POST' else None
    
    # Calculate totals with selected shipping
    items = list(cart.items())
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    totals = cart.totals(shipping_method=shipping_method, destination_state=destination_state)
    
    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('catalog:list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            if request.user.is_authenticated:
                addr.user = request.user
            addr.save()

            # Calculate total weight for the order
            total_weight = sum(
                (item['product'].weight or Decimal('0.5')) * item['quantity'] 
                for item in items
            )

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=request.user.email if request.user.is_authenticated else request.POST.get('email', ''),
                shipping_address=addr,
                subtotal=totals['subtotal'],
                shipping_cost=totals['shipping'],
                total=totals['total'],
                shipping_method=shipping_method,
                total_weight=total_weight,
            )
            for i in items:
                OrderItem.objects.create(
                    order=order,
                    product=i['product'],
                    quantity=i['quantity'],
                    unit_price=i['price'],
                )

            # Initialize a Paystack transaction and redirect the user
            try:
                callback = settings.PAYSTACK_CALLBACK_URL or request.build_absolute_uri(reverse('orders:verify_paystack'))
                # Get customer details from the address
                full_name = addr.full_name
                phone_number = addr.phone
                
                init = initialize_transaction(
                    totals['total'],
                    order.email,
                    reference=f"order_{order.pk}",
                    callback_url=callback,
                    full_name=full_name,
                    phone_number=phone_number
                )
                # Paystack returns an authorization_url to redirect the customer to
                auth_url = init.get('authorization_url')
                # Store the returned reference on the order for later verification (reuse stripe_payment_intent field)
                # order.stripe_payment_intent = init.get('reference') or ''
                order.save()
                return HttpResponseRedirect(auth_url)
            except Exception as e:
                messages.error(request, f"Payment initialization failed: {e}")
                # Let user retry or return to checkout
                return redirect('orders:checkout')
    else:
        form = CheckoutForm()
        # Get all shipping options to display
        items = list(cart.items())
        subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in items)
        shipping_options = get_all_shipping_options(items, destination_state, subtotal)

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart_items': items,
        'totals': totals,
        'shipping_options': shipping_options,
        'selected_shipping_method': shipping_method,

    })
