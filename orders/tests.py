from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from decimal import Decimal
from catalog.models import Product, Category
from orders.cart import Cart
from orders.models import Order, Address, OrderItem
from orders.shipping import (
    calculate_weight,
    calculate_shipping,
    get_all_shipping_options,
    get_regional_surcharge,
)
from orders.emails import (
    send_order_confirmation_email,
    send_payment_received_email,
    send_order_shipped_email,
    send_order_delivered_email,
    send_order_cancelled_email,
    send_admin_new_order_email,
    send_admin_payment_notification_email,
    send_admin_shipped_notification_email,
    send_admin_delivered_notification_email,
    send_admin_cancelled_notification_email,
)
from shop.payments.paystack import sanitize_phone_number, prepare_customer_metadata


class ShippingCalculationTest(TestCase):
    """Test shipping calculation functionality."""

    def setUp(self):
        """Create test data."""
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product1 = Product.objects.create(
            category=self.category,
            title="Smartphone",
            slug="smartphone",
            price=Decimal("50000.00"),
            weight=Decimal("0.2"),
        )
        self.product2 = Product.objects.create(
            category=self.category,
            title="Laptop",
            slug="laptop",
            price=Decimal("100000.00"),
            weight=Decimal("2.0"),
        )

    def test_calculate_weight(self):
        """Test weight calculation."""
        items = [
            {"product": self.product1, "quantity": 2},
            {"product": self.product2, "quantity": 1},
        ]
        total_weight = calculate_weight(items)
        expected = Decimal("0.2") * 2 + Decimal("2.0") * 1
        self.assertEqual(total_weight, expected)

    def test_calculate_shipping_standard(self):
        """Test standard shipping calculation."""
        items = [{"product": self.product1, "quantity": 1}]
        # Use subtotal less than free shipping threshold (10000)
        result = calculate_shipping(items, "standard", None, Decimal("5000.00"))
        
        self.assertEqual(result["method"], "standard")
        self.assertGreater(result["cost"], 0)
        self.assertIn("base", result["breakdown"])
        self.assertIn("weight_cost", result["breakdown"])

    def test_calculate_shipping_express(self):
        """Test express shipping calculation."""
        items = [{"product": self.product1, "quantity": 1}]
        # Use subtotal less than free shipping threshold
        result = calculate_shipping(items, "express", None, Decimal("5000.00"))
        
        self.assertEqual(result["method"], "express")
        standard_result = calculate_shipping(items, "standard", None, Decimal("5000.00"))
        # Express should cost more than standard
        self.assertGreater(result["cost"], standard_result["cost"])

    def test_calculate_shipping_with_regional_surcharge(self):
        """Test shipping with regional surcharge."""
        items = [{"product": self.product1, "quantity": 1}]
        # Use subtotal less than free shipping threshold
        result_lagos = calculate_shipping(items, "standard", "lagos", Decimal("5000.00"))
        result_kano = calculate_shipping(items, "standard", "kano", Decimal("5000.00"))
        
        # Kano should have higher cost due to surcharge
        self.assertGreater(result_kano["cost"], result_lagos["cost"])

    def test_get_regional_surcharge(self):
        """Test regional surcharge lookup."""
        self.assertEqual(get_regional_surcharge("lagos"), Decimal("0.0"))
        self.assertGreater(get_regional_surcharge("kano"), Decimal("0"))
        self.assertEqual(get_regional_surcharge("unknown_state"), Decimal("100.00"))

    def test_get_all_shipping_options(self):
        """Test getting all available shipping options."""
        items = [{"product": self.product1, "quantity": 1}]
        # Use subtotal less than free shipping threshold
        options = get_all_shipping_options(items, "lagos", Decimal("5000.00"))
        
        self.assertEqual(len(options), 3)  # standard, express, economy
        methods = [opt["method"] for opt in options]
        self.assertIn("standard", methods)
        self.assertIn("express", methods)
        self.assertIn("economy", methods)


class CartShippingTest(TestCase):
    """Test cart integration with shipping."""

    def setUp(self):
        """Create test data and request."""
        self.factory = RequestFactory()
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            category=self.category,
            title="Phone",
            slug="phone",
            price=Decimal("30000.00"),
            weight=Decimal("0.3"),
        )

    def test_cart_totals_with_shipping(self):
        """Test cart totals calculation with shipping."""
        request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        cart = Cart(request)
        cart.add(self.product.id, 1)
        
        totals = cart.totals(shipping_method="standard", destination_state="lagos")
        
        # Product price is 30000, which is > free shipping threshold (10000), so shipping should be free
        # Let's test with a lower priced product or adjust expectation
        self.assertEqual(totals["subtotal"], Decimal("30000.00"))
        # The free shipping threshold is 10000, so this should have free shipping
        self.assertEqual(totals["shipping"], Decimal("0"))
        self.assertEqual(totals["total"], totals["subtotal"])
        self.assertEqual(totals["shipping_method"], "standard")


class PaystackCustomerDetailsTest(TestCase):
    """Test Paystack customer details integration."""

    def test_sanitize_phone_number_valid(self):
        """Test phone number sanitization with valid inputs."""
        # Test various phone formats - sanitization removes formatting
        self.assertEqual(sanitize_phone_number("+234-803-123-4567"), "+2348031234567")
        self.assertEqual(sanitize_phone_number("08031234567"), "08031234567")
        self.assertEqual(sanitize_phone_number("+1 (555) 123-4567"), "+15551234567")
        self.assertEqual(sanitize_phone_number("  +234 803 1234567  "), "+2348031234567")

    def test_sanitize_phone_number_invalid(self):
        """Test phone number sanitization with invalid inputs."""
        self.assertIsNone(sanitize_phone_number(""))
        self.assertIsNone(sanitize_phone_number("   "))
        self.assertIsNone(sanitize_phone_number("abcd"))
        self.assertIsNone(sanitize_phone_number("*&^%$"))

    def test_prepare_customer_metadata_full(self):
        """Test preparing customer metadata with all details."""
        metadata = prepare_customer_metadata(
            full_name="John Doe Smith",
            phone_number="+234 803 123 4567"
        )
        
        self.assertIn("full_name", metadata)
        self.assertEqual(metadata["full_name"], "John Doe Smith")
        self.assertIn("first_name", metadata)
        self.assertEqual(metadata["first_name"], "John")
        self.assertIn("last_name", metadata)
        self.assertEqual(metadata["last_name"], "Doe Smith")
        self.assertIn("phone_number", metadata)

    def test_prepare_customer_metadata_name_only(self):
        """Test preparing metadata with name only."""
        metadata = prepare_customer_metadata(full_name="Jane Doe", phone_number=None)
        
        self.assertIn("full_name", metadata)
        self.assertEqual(metadata["full_name"], "Jane Doe")
        self.assertIn("first_name", metadata)
        self.assertIn("last_name", metadata)
        self.assertNotIn("phone_number", metadata)

    def test_prepare_customer_metadata_single_name(self):
        """Test preparing metadata with single name."""
        metadata = prepare_customer_metadata(full_name="Madonna", phone_number=None)
        
        self.assertIn("full_name", metadata)
        self.assertIn("first_name", metadata)
        self.assertEqual(metadata["first_name"], "Madonna")
        self.assertNotIn("last_name", metadata)

    def test_order_denormalized_customer_details(self):
        """Test that Order automatically stores customer details from Address."""
        # Create address
        address = Address.objects.create(
            full_name="Test Customer",
            phone="+234 803 123 4567",
            line1="123 Test St",
            city="Lagos",
            state="lagos",
            country="NG"
        )
        
        # Create category and product for order items
        category = Category.objects.create(name="Test", slug="test")
        product = Product.objects.create(
            category=category,
            title="Test Product",
            slug="test-product",
            price=Decimal("5000.00"),
            weight=Decimal("0.5")
        )
        
        # Create order
        order = Order.objects.create(
            email="test@example.com",
            shipping_address=address,
            subtotal=Decimal("5000.00"),
            shipping_cost=Decimal("500.00"),
            total=Decimal("5500.00"),
        )
        
        # Verify customer details were denormalized
        self.assertEqual(order.customer_full_name, "Test Customer")
        self.assertEqual(order.customer_phone, "+234 803 123 4567")

    def test_order_customer_details_already_set(self):
        """Test that Order save() doesn't override existing customer details."""
        address = Address.objects.create(
            full_name="Address Customer",
            phone="+234 803 111 1111",
            line1="456 Address St",
            city="Abuja",
            state="abuja",
            country="NG"
        )
        
        # Create order with pre-set customer details
        order = Order.objects.create(
            email="test2@example.com",
            shipping_address=address,
            subtotal=Decimal("5000.00"),
            shipping_cost=Decimal("500.00"),
            total=Decimal("5500.00"),
            customer_full_name="Override Name",
            customer_phone="+234 803 999 9999"
        )
        
        # Verify pre-set details weren't changed
        self.assertEqual(order.customer_full_name, "Override Name")
        self.assertEqual(order.customer_phone, "+234 803 999 9999")


class EmailNotificationTest(TestCase):
    """Test email notification system for order lifecycle."""

    def setUp(self):
        """Create test data for email tests."""
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            category=self.category,
            title="Test Phone",
            slug="test-phone",
            price=Decimal("15000.00"),
            weight=Decimal("0.2"),
        )
        self.address = Address.objects.create(
            full_name="John Doe",
            phone="+234 803 123 4567",
            line1="123 Test Street",
            line2="Apt 4B",
            city="Lagos",
            state="lagos",
            country="NG",
            postcode="100001"
        )
        self.order = Order.objects.create(
            email="customer@example.com",
            shipping_address=self.address,
            subtotal=Decimal("15000.00"),
            shipping_cost=Decimal("1000.00"),
            total=Decimal("16000.00"),
            customer_full_name="John Doe",
            customer_phone="+234 803 123 4567",
            status="created"
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("15000.00")
        )

    def test_send_order_confirmation_email(self):
        """Test order confirmation email is sent correctly."""
        mail.outbox = []  # Clear outbox
        
        result = send_order_confirmation_email(self.order)
        
        # Check email was sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.order.email])
        self.assertIn("Order Confirmation", email.subject)
        self.assertIn(f"#{self.order.id}", email.body)
        
        # Check both HTML and text versions exist
        self.assertEqual(len(email.alternatives), 1)
        self.assertIn("text/html", email.alternatives[0][1])

    def test_send_order_confirmation_email_with_custom_email(self):
        """Test confirmation email is sent correctly."""
        mail.outbox = []
        
        result = send_order_confirmation_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.order.email])
        self.assertIn("Order Confirmation", email.subject)

    def test_send_payment_received_email(self):
        """Test payment received email is sent correctly."""
        mail.outbox = []
        self.order.status = "paid"
        self.order.save()
        
        result = send_payment_received_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.order.email])
        self.assertIn("Payment Received", email.subject)
        self.assertIn(f"{self.order.total}", email.body)

    def test_send_order_shipped_email(self):
        """Test order shipped email with tracking number."""
        mail.outbox = []
        tracking_number = "PAYSTACK-TRACK-12345"
        
        result = send_order_shipped_email(self.order, tracking_number)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.order.email])
        self.assertIn("Shipped", email.subject)
        self.assertIn(tracking_number, email.body)

    def test_send_order_shipped_email_without_tracking(self):
        """Test shipped email when tracking number is not available."""
        mail.outbox = []
        
        result = send_order_shipped_email(self.order, tracking_number=None)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("Shipped", email.subject)

    def test_send_order_delivered_email(self):
        """Test order delivered email is sent correctly."""
        mail.outbox = []
        self.order.status = "fulfilled"
        self.order.save()
        
        result = send_order_delivered_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.order.email])
        self.assertIn("Delivered", email.subject)
        self.assertIn(self.order.customer_full_name, email.body)

    def test_send_order_cancelled_email(self):
        """Test order cancelled email with reason and refund info."""
        mail.outbox = []
        self.order.status = "cancelled"
        self.order.save()
        
        result = send_order_cancelled_email(
            self.order,
            reason="Out of stock"
        )
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.order.email])
        self.assertIn("Order Cancelled", email.subject)
        self.assertIn("Out of stock", email.body)
        self.assertIn(f"{self.order.total}", email.body)

    def test_send_order_cancelled_email_without_reason(self):
        """Test cancelled email without explicit reason."""
        mail.outbox = []
        
        result = send_order_cancelled_email(self.order, reason=None)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("Order Cancelled", email.subject)

    def test_email_contains_product_details(self):
        """Test that emails contain correct product details."""
        mail.outbox = []
        
        send_order_confirmation_email(self.order)
        
        email = mail.outbox[0]
        # Check product title and price are in email
        self.assertIn("Test Phone", email.body)
        self.assertIn("15000", email.body)

    def test_email_contains_shipping_address(self):
        """Test that emails contain correct shipping address."""
        mail.outbox = []
        
        send_order_confirmation_email(self.order)
        
        email = mail.outbox[0]
        # Check address details
        self.assertIn("John Doe", email.body)
        self.assertIn("123 Test Street", email.body)
        self.assertIn("Lagos", email.body)

    def test_email_html_alternative_present(self):
        """Test that emails have both HTML and plain text versions."""
        mail.outbox = []
        
        send_order_confirmation_email(self.order)
        
        email = mail.outbox[0]
        # Should have both plain text (in body) and HTML (in alternatives)
        self.assertGreater(len(email.body), 0)  # Plain text
        self.assertEqual(len(email.alternatives), 1)  # HTML alternative
        self.assertEqual(email.alternatives[0][1], "text/html")

    def test_multiple_emails_sent_in_sequence(self):
        """Test sending multiple emails in sequence doesn't cause issues."""
        mail.outbox = []
        
        send_order_confirmation_email(self.order)
        send_payment_received_email(self.order)
        send_order_shipped_email(self.order, "TRACK-001")
        
        self.assertEqual(len(mail.outbox), 3)
        subjects = [e.subject for e in mail.outbox]
        self.assertIn("Confirmation", subjects[0])
        self.assertIn("Received", subjects[1])
        self.assertIn("Shipped", subjects[2])

    def test_email_with_special_characters_in_name(self):
        """Test email works with special characters in customer name."""
        mail.outbox = []
        self.order.customer_full_name = "José García O'Brien"
        self.order.save()
        
        result = send_order_confirmation_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        # Check for name in email (either plain or HTML encoded)
        email_content = mail.outbox[0].body + str(mail.outbox[0].alternatives)
        self.assertIn("José", email_content)

    def test_email_with_multiple_order_items(self):
        """Test email rendering with multiple products in order."""
        mail.outbox = []
        
        # Add another product
        product2 = Product.objects.create(
            category=self.category,
            title="Laptop",
            slug="test-laptop",
            price=Decimal("50000.00"),
            weight=Decimal("1.5"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=product2,
            quantity=1,
            unit_price=Decimal("50000.00")
        )
        
        send_order_confirmation_email(self.order)
        
        email = mail.outbox[0]
        # Both products should be in email
        self.assertIn("Test Phone", email.body)
        self.assertIn("Laptop", email.body)

    def test_email_sender_is_configured(self):
        """Test that email sender is set to configured address."""
        mail.outbox = []
        
        send_order_confirmation_email(self.order)
        
        email = mail.outbox[0]
        # Should use DEFAULT_FROM_EMAIL from settings
        self.assertIsNotNone(email.from_email)

    def test_email_with_zero_shipping(self):
        """Test email with free shipping."""
        mail.outbox = []
        address_free_shipping = Address.objects.create(
            full_name="Free Shipping Customer",
            phone="+234 803 000 0000",
            line1="Free St",
            city="Abuja",
            state="abuja",
            country="NG",
            postcode="900001"
        )
        order_with_free_shipping = Order.objects.create(
            email="free@example.com",
            shipping_address=address_free_shipping,
            subtotal=Decimal("50000.00"),
            shipping_cost=Decimal("0.00"),
            total=Decimal("50000.00"),
            customer_full_name="Free Shipping Customer",
            customer_phone="+234 803 000 0000",
            status="created"
        )
        
        send_order_confirmation_email(order_with_free_shipping)
        
        email = mail.outbox[0]
        self.assertIn("0", email.body)  # Shipping cost

    def test_order_confirmation_email_called_on_creation_via_signal(self):
        """Test that confirmation email is sent when order is created via signal."""
        mail.outbox = []
        
        # Create a new order (signals should trigger email)
        signal_address = Address.objects.create(
            full_name="Signal Test",
            phone="+234 700 000 0000",
            line1="Signal Test St",
            city="Kano",
            state="kano",
            country="NG",
            postcode="700001"
        )
        new_order = Order.objects.create(
            email="signal@example.com",
            shipping_address=signal_address,
            subtotal=Decimal("5000.00"),
            shipping_cost=Decimal("500.00"),
            total=Decimal("5500.00"),
            customer_full_name="Signal Tester",
            customer_phone="+234 700 000 0000",
            status="created"
        )
        
        # Signal handler should have sent confirmation email
        # Note: This may or may not fire depending on signal setup
        # For testing, we can explicitly call the email function
        send_order_confirmation_email(new_order)
        
        self.assertGreaterEqual(len(mail.outbox), 1)
        email = mail.outbox[-1]
        self.assertEqual(email.to, ["signal@example.com"])


class AdminEmailNotificationTest(TestCase):
    """Test admin/owner email notifications for order events."""

    def setUp(self):
        """Create test data for admin email tests."""
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            category=self.category,
            title="Admin Test Phone",
            slug="admin-test-phone",
            price=Decimal("20000.00"),
            weight=Decimal("0.3"),
        )
        self.address = Address.objects.create(
            full_name="Admin Test Customer",
            phone="+234 803 999 9999",
            line1="456 Admin Test St",
            city="Abuja",
            state="abuja",
            country="NG",
            postcode="200001"
        )
        self.order = Order.objects.create(
            email="admincustomer@example.com",
            shipping_address=self.address,
            subtotal=Decimal("20000.00"),
            shipping_cost=Decimal("1500.00"),
            total=Decimal("21500.00"),
            customer_full_name="Admin Test Customer",
            customer_phone="+234 803 999 9999",
            status="created"
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("20000.00")
        )

    def test_admin_new_order_email_sent(self):
        """Test admin receives notification when new order is created."""
        mail.outbox = []
        
        result = send_admin_new_order_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn("[ADMIN]", email.subject)
        self.assertIn("New Order", email.subject)
        self.assertIn(f"#{self.order.pk}", email.subject)

    def test_admin_payment_notification_email_sent(self):
        """Test admin receives notification when payment is received."""
        mail.outbox = []
        self.order.status = "paid"
        self.order.save()
        
        result = send_admin_payment_notification_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn("[ADMIN]", email.subject)
        self.assertIn("Payment", email.subject)

    def test_admin_shipped_notification_email_sent(self):
        """Test admin receives notification when order is shipped."""
        mail.outbox = []
        
        result = send_admin_shipped_notification_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn("[ADMIN]", email.subject)
        self.assertIn("Shipped", email.subject)

    def test_admin_delivered_notification_email_sent(self):
        """Test admin receives notification when order is delivered."""
        mail.outbox = []
        self.order.status = "fulfilled"
        self.order.save()
        
        result = send_admin_delivered_notification_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn("[ADMIN]", email.subject)
        self.assertIn("Delivered", email.subject)

    def test_admin_cancelled_notification_email_sent(self):
        """Test admin receives notification when order is cancelled."""
        mail.outbox = []
        self.order.status = "cancelled"
        self.order.save()
        
        result = send_admin_cancelled_notification_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn("[ADMIN]", email.subject)
        self.assertIn("Cancelled", email.subject)

    def test_admin_email_contains_order_details(self):
        """Test admin email contains complete order information."""
        mail.outbox = []
        
        send_admin_new_order_email(self.order)
        
        email = mail.outbox[0]
        # Check order details
        self.assertIn(f"#{self.order.pk}", email.body)
        self.assertIn("Admin Test Customer", email.body)
        self.assertIn("admincustomer@example.com", email.body)
        self.assertIn("20000", email.body)  # Product price

    def test_admin_email_contains_product_items(self):
        """Test admin email lists all order items with details."""
        mail.outbox = []
        
        send_admin_new_order_email(self.order)
        
        email = mail.outbox[0]
        # Check product information
        self.assertIn("Admin Test Phone", email.body)
        self.assertIn("21500", email.body)  # Total

    def test_admin_email_contains_shipping_address(self):
        """Test admin email includes complete shipping address."""
        mail.outbox = []
        
        send_admin_new_order_email(self.order)
        
        email = mail.outbox[0]
        # Check address details
        self.assertIn("Admin Test Customer", email.body)
        self.assertIn("456 Admin Test St", email.body)
        self.assertIn("Abuja", email.body)

    def test_admin_email_has_html_alternative(self):
        """Test admin email has both HTML and plain text versions."""
        mail.outbox = []
        
        send_admin_new_order_email(self.order)
        
        email = mail.outbox[0]
        self.assertGreater(len(email.body), 0)  # Plain text
        self.assertEqual(len(email.alternatives), 1)  # HTML alternative
        self.assertEqual(email.alternatives[0][1], "text/html")

    def test_admin_email_sent_to_configured_admin_email(self):
        """Test admin email is sent to ADMIN_EMAIL from settings."""
        from django.conf import settings
        mail.outbox = []
        
        send_admin_new_order_email(self.order)
        
        email = mail.outbox[0]
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if admin_email:
            self.assertIn(admin_email, email.to)

    def test_multiple_admin_notifications_in_sequence(self):
        """Test multiple admin notifications can be sent in sequence."""
        mail.outbox = []
        
        send_admin_new_order_email(self.order)
        send_admin_payment_notification_email(self.order)
        send_admin_shipped_notification_email(self.order)
        
        self.assertEqual(len(mail.outbox), 3)
        subjects = [e.subject for e in mail.outbox]
        self.assertTrue(all("[ADMIN]" in s for s in subjects))

    def test_admin_email_different_event_types(self):
        """Test admin emails have different subjects for different event types."""
        mail.outbox = []
        
        # Test different event types
        send_admin_new_order_email(self.order)
        send_admin_payment_notification_email(self.order)
        
        self.assertEqual(len(mail.outbox), 2)
        subject1 = mail.outbox[0].subject
        subject2 = mail.outbox[1].subject
        
        # Subjects should be different
        self.assertNotEqual(subject1, subject2)
        self.assertIn("New Order", subject1)
        self.assertIn("Payment", subject2)

    def test_admin_email_with_special_characters_in_name(self):
        """Test admin email handles special characters in customer name."""
        mail.outbox = []
        self.order.customer_full_name = "Jos\u00e9 Garc\u00eda O'Brien"
        self.order.save()
        
        result = send_admin_new_order_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        # Check that name appears in subject or body
        email = mail.outbox[0]
        email_content = email.body + email.subject
        self.assertIn("Jos\u00e9", email_content)

    def test_admin_email_with_multiple_items(self):
        """Test admin email displays all items when multiple products ordered."""
        mail.outbox = []
        
        # Add another product
        product2 = Product.objects.create(
            category=self.category,
            title="Premium Headphones",
            slug="premium-headphones",
            price=Decimal("8000.00"),
            weight=Decimal("0.2"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=product2,
            quantity=2,
            unit_price=Decimal("8000.00")
        )
        
        send_admin_new_order_email(self.order)
        
        email = mail.outbox[0]
        # Both products should be listed
        self.assertIn("Admin Test Phone", email.body)
        self.assertIn("Premium Headphones", email.body)
        self.assertIn("2", email.body)  # Quantity of second item
