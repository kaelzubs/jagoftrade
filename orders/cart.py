from decimal import Decimal
from catalog.models import Product
from orders.shipping import calculate_shipping


class Cart: 
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get("cart")
        if not cart:
            cart = self.session["cart"] = {}
        self.cart = cart
        
    def add(self, product_id, quantity=1):
        product = Product.objects.get(id=product_id)
        item = self.cart.get(str(product_id), {'quantity': 0, 'price': str(product.price), 'title': product.title})
        item['quantity'] += quantity
        self.cart[str(product_id)] = item
        self.save()

    def remove(self, product_id):
        self.cart.pop(str(product_id), None)
        self.save()

    def clear(self):
        self.session['cart'] = {}
        self.save()

    def __len__(self):
        """Return total quantity of items in the cart"""
        return sum(item["quantity"] for item in self.cart.values())
    
    def save(self):
        self.session.modified = True
 
    def items(self):
        product_ids = [int(pid) for pid in self.cart.keys()]
        products = Product.objects.filter(id__in=product_ids)
        for p in products:
            data = self.cart[str(p.id)]
            yield {
                'title': data['title'],
                'product': p,
                'quantity': data['quantity'],
                'price': Decimal(data['price']),
                'line_total': Decimal(data['price']) * data['quantity'],
            }

    def totals(self, shipping_method="standard", destination_state=None):
        """
        Calculate cart totals including dynamic shipping.
        
        Args:
            shipping_method: 'standard', 'express', or 'economy'
            destination_state: customer's state for shipping surcharge
        """
        items_list = list(self.items())
        subtotal = sum(Decimal(i['price']) * i['quantity'] for i in items_list)
        
        # Calculate shipping dynamically
        shipping_calc = calculate_shipping(
            items_list,
            shipping_method=shipping_method,
            destination_state=destination_state,
            cart_subtotal=subtotal
        )
        shipping = shipping_calc['cost']
        
        total = subtotal + shipping
        return {
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'shipping_method': shipping_method,
            'shipping_breakdown': shipping_calc.get('breakdown', {}),
        }