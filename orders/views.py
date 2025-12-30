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

@login_required
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

def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/success.html', {'order': order})


def calculate_shipping_api(request):
    """
    API endpoint for AJAX calls to calculate shipping dynamically.
    Expects GET parameters:
    - shipping_method: 'standard', 'express', or 'economy'
    - state: destination state
    Returns JSON with shipping cost and breakdown.
    """
    shipping_method = request.GET.get('shipping_method', 'standard')
    destination_state = request.GET.get('state', '')
    
    cart = Cart(request)
    items = list(cart.items())
    subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in items)
    
    if not items:
        return JsonResponse({'error': 'Cart is empty'}, status=400)
    
    from orders.shipping import calculate_shipping
    result = calculate_shipping(items, shipping_method, destination_state, Decimal(str(subtotal)))
    
    return JsonResponse({
        'cost': float(result['cost']),
        'method': result['method'],
        'method_name': result['method_name'],
        'est_days': result['est_days'],
        'total_weight': float(result['total_weight']),
        'breakdown': {
            'base': float(result['breakdown']['base']),
            'weight_cost': float(result['breakdown']['weight_cost']),
            'regional_surcharge': float(result['breakdown']['regional_surcharge']),
            'subtotal': float(result['breakdown']['subtotal']),
            'free_shipping_applied': result['breakdown']['free_shipping_applied'],
        },
    })


def verify_paystack(request):
    """Callback endpoint for Paystack to redirect after payment.
    Expects a `reference` GET parameter.
    """
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, 'Missing payment reference from Paystack.')
        return redirect('orders:checkout')

    try:
        data = verify_transaction(reference)
    except Exception as e:
        messages.error(request, f'Payment verification failed: {e}')
        return redirect('orders:checkout')

    # expected metadata or amount can be checked here
    # Find corresponding order by stored reference
    order = Order.objects.filter(stripe_payment_intent__iexact=reference).first()
    if not order:
        # Try matching reference prefix order_<id>
        if reference.startswith('order_'):
            try:
                oid = int(reference.split('_', 1)[1])
                order = Order.objects.filter(id=oid).first()
            except Exception:
                order = None

    if not order:
        messages.error(request, 'Order not found for payment reference.')
        return redirect('core:home')

    status = data.get('status')
    # Paystack returns 'success' for successful payments
    if status == 'success' or data.get('status') == 'success':
        order.status = 'paid'
        order.stripe_payment_intent = reference
        order.save()  # This triggers the signal to send payment email
        # clear cart now that payment succeeded
        try:
            cart = Cart(request)
            cart.clear()
        except Exception:
            pass
        messages.success(request, 'Payment successful. Thank you!')
        return redirect('orders:success', order_id=order.pk)
    else:
        messages.error(request, 'Payment not successful.')
        return redirect('orders:checkout')


def update_cart_qty(request):
    """
    AJAX endpoint to update cart item quantity.
    Accepts both single updates and bulk updates.
    Single: POST with JSON: {'product_id': int, 'quantity': int}
    Bulk: POST with JSON: [{'product_id': int, 'quantity': int}, ...]
    Returns JSON response with success status.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        cart = Cart(request)
        
        # Handle both single and bulk updates
        updates = data if isinstance(data, list) else [data]
        
        for update in updates:
            product_id = int(update.get('product_id'))
            new_qty = int(update.get('quantity'))
            
            if new_qty < 1:
                return JsonResponse({'success': False, 'message': f'Quantity for product {product_id} must be at least 1'})
            
            # Get the product to verify it exists
            product = Product.objects.get(id=product_id)
            
            # Update quantity in cart
            if str(product_id) in cart.cart:
                cart.cart[str(product_id)]['quantity'] = new_qty
            else:
                return JsonResponse({'success': False, 'message': f'Product {product_id} not in cart'})
        
        # Save cart after all updates
        cart.save()
        return JsonResponse({'success': True, 'message': 'Quantities updated successfully'})
    
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    except (ValueError, json.JSONDecodeError) as e:
        return JsonResponse({'success': False, 'message': f'Invalid request: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
