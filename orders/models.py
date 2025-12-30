from django.conf import settings
from django.db import models
from catalog.models import Product

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, default='NG')  # ISO-2
    phone = models.CharField(max_length=25, blank=True)

    def __str__(self): return f'{self.full_name}, {self.line1}, {self.city}'

class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('sent_to_supplier', 'Sent to supplier'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='shipping_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stripe_payment_intent = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    aliexpress_order_id = models.CharField(max_length=255, null=True, blank=True)
    tracking_number = models.CharField(max_length=255, null=True, blank=True)
    # Shipping tracking
    shipping_method = models.CharField(max_length=20, default='standard', choices=[('standard', 'Standard'), ('express', 'Express'), ('economy', 'Economy')])
    total_weight = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Total weight of order in kg")
    # Customer details (denormalized from Address for easier access/reporting)
    customer_full_name = models.CharField(max_length=120, blank=True, help_text="Customer's full name at time of order")
    customer_phone = models.CharField(max_length=25, blank=True, help_text="Customer's phone number at time of order")

    def __str__(self): return f'Order #{self.pk}'
    
    def get_total_items(self):
        """Return total quantity of items in the order."""
        return sum(item.quantity for item in self.items.all())
    
    def get_total_item_value(self):
        """Return sum of all line totals (subtotal of items)."""
        return sum(item.line_total() for item in self.items.all())
    
    def save(self, *args, **kwargs):
        """Automatically populate customer details from shipping address if not already set."""
        if not self.customer_full_name and self.shipping_address:
            self.customer_full_name = self.shipping_address.full_name
        if not self.customer_phone and self.shipping_address:
            self.customer_phone = self.shipping_address.phone
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def line_total(self):
        return self.unit_price * self.quantity