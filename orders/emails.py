from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Order
import logging

logger = logging.getLogger(__name__)

def _get_order_title(order):
    """Generate a short human-friendly title for an order.

    Strategy:
    - If there are no items, return "Order #<id>"
    - If only one item, return "<qty>x <product title>"
    - If multiple items, return "<qty>x <first product title> +N more"
    """
    try:
        items = list(order.items.all())
        if not items:
            return f"Order #{order.pk}"
        first = items[0]
        title = first.product.title if getattr(first.product, 'title', None) else str(first.product)
        qty = getattr(first, 'quantity', 1)
        if len(items) == 1:
            return f"{qty}x {title}"
        else:
            return f"{qty}x {title} +{len(items)-1} more"
    except Exception:
        return f"Order #{order.pk}"


def send_order_confirmation_email(order):
    """
    Send order confirmation email to customer after successful purchase.
    Includes order summary, items, and payment details.
    """
    try:
        # Prepare context for email template
        order_title = _get_order_title(order)
        total_items = order.get_total_items()
        total_item_value = order.get_total_item_value()
        context = {
            'order': order,
            'order_items': order.items.all(),
            'order_title': order_title,
            'customer_name': order.customer_full_name or order.email,
            'order_total': order.total,
            'order_subtotal': order.subtotal,
            'shipping_cost': order.shipping_cost,
            'shipping_address': order.shipping_address,
            'total_items': total_items,
            'total_item_value': total_item_value,
            'site_name': 'TechRideMobile',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        # Render HTML and plain text versions
        html_content = render_to_string('orders/emails/order_confirmation.html', context)
        text_content = render_to_string('orders/emails/order_confirmation.txt', context)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=f'Order Confirmation - Order #{order.pk} - {order_title}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        logger.info(f"Order confirmation email sent for Order #{order.pk} to {order.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for Order #{order.pk}: {str(e)}")
        return False


def send_payment_received_email(order):
    """
    Send payment received confirmation email.
    Includes order number, amount, and next steps.
    """
    try:
        order_title = _get_order_title(order)
        context = {
            'order': order,
            'order_title': order_title,
            'customer_name': order.customer_full_name or order.email,
            'order_total': order.total,
            'order_number': order.pk,
            'site_name': 'TechRideMobile',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        html_content = render_to_string('orders/emails/payment_received.html', context)
        text_content = render_to_string('orders/emails/payment_received.txt', context)
        
        email = EmailMultiAlternatives(
            subject=f'Payment Received - Order #{order.pk} - {order_title}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Payment received email sent for Order #{order.pk} to {order.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send payment received email for Order #{order.pk}: {str(e)}")
        return False


def send_order_shipped_email(order, tracking_number=None):
    """
    Send shipment notification email with tracking information.
    """
    try:
        order_title = _get_order_title(order)
        context = {
            'order': order,
            'order_items': order.items.all(),
            'order_title': order_title,
            'customer_name': order.customer_full_name or order.email,
            'tracking_number': tracking_number or order.tracking_number,
            'shipping_address': order.shipping_address,
            'estimated_delivery': f'{settings.SHIPPING_ESTIMATED_DAYS[0]}-{settings.SHIPPING_ESTIMATED_DAYS[1]} days',
            'site_name': 'TechRideMobile',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        html_content = render_to_string('orders/emails/order_shipped.html', context)
        text_content = render_to_string('orders/emails/order_shipped.txt', context)
        
        email = EmailMultiAlternatives(
            subject=f'Your Order is Shipped - Order #{order.pk} - {order_title}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Shipment email sent for Order #{order.pk} to {order.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send shipment email for Order #{order.pk}: {str(e)}")
        return False


def send_order_delivered_email(order):
    """
    Send order delivered notification email.
    """
    try:
        context = {
            'order': order,
            'customer_name': order.customer_full_name or order.email,
            'order_number': order.pk,
            'site_name': 'TechRideMobile',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        html_content = render_to_string('orders/emails/order_delivered.html', context)
        text_content = render_to_string('orders/emails/order_delivered.txt', context)
        
        email = EmailMultiAlternatives(
            subject=f'Order Delivered - Order #{order.pk}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Delivered email sent for Order #{order.pk} to {order.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send delivered email for Order #{order.pk}: {str(e)}")
        return False


def send_order_cancelled_email(order, reason=''):
    """
    Send order cancellation notification email.
    """
    try:
        order_title = _get_order_title(order)
        context = {
            'order': order,
            'order_title': order_title,
            'customer_name': order.customer_full_name or order.email,
            'order_number': order.pk,
            'cancellation_reason': reason,
            'refund_amount': order.total,
            'site_name': 'TechRideMobile',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        html_content = render_to_string('orders/emails/order_cancelled.html', context)
        text_content = render_to_string('orders/emails/order_cancelled.txt', context)
        
        email = EmailMultiAlternatives(
            subject=f'Order Cancelled - Order #{order.pk} - {order_title}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Cancellation email sent for Order #{order.pk} to {order.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send cancellation email for Order #{order.pk}: {str(e)}")
        return False


def send_admin_order_notification_email(order, event_type='created'):
    """
    Send order notification email to admin/owner.
    Notifies shop owner about new orders and status changes.
    
    Args:
        order: Order object
        event_type: 'created', 'paid', 'shipped', 'delivered', or 'cancelled'
    """
    try:
        # Get admin email from settings
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if not admin_email:
            logger.warning(f"ADMIN_EMAIL not configured in settings")
            return False
        
        # Prepare context for email template
        order_title = _get_order_title(order)
        total_items = order.get_total_items()
        total_item_value = order.get_total_item_value()
        context = {
            'order': order,
            'order_items': order.items.all(),
            'order_title': order_title,
            'customer_name': order.customer_full_name or order.email,
            'customer_email': order.email,
            'customer_phone': order.customer_phone,
            'order_total': order.total,
            'order_subtotal': order.subtotal,
            'shipping_cost': order.shipping_cost,
            'shipping_address': order.shipping_address,
            'total_items': total_items,
            'total_item_value': total_item_value,
            'event_type': event_type,
            'site_name': 'TechRideMobile',
            'site_admin_url': getattr(settings, 'SITE_ADMIN_URL', '/admin/'),
        }
        
        # Render HTML and plain text versions
        html_content = render_to_string('orders/emails/admin_order_notification.html', context)
        text_content = render_to_string('orders/emails/admin_order_notification.txt', context)
        
        # Create email with descriptive subject
        event_labels = {
            'created': 'New Order Received',
            'paid': 'Payment Received',
            'shipped': 'Order Shipped',
            'delivered': 'Order Delivered',
            'cancelled': 'Order Cancelled',
        }
        event_label = event_labels.get(event_type, 'Order Updated')
        
        email = EmailMultiAlternatives(
            subject=f'[ADMIN] {event_label} - Order #{order.pk} - {order_title} from {order.customer_full_name or order.email}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        logger.info(f"Admin notification email sent for Order #{order.pk} ({event_type}) to {admin_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin notification email for Order #{order.pk}: {str(e)}")
        return False


def send_admin_new_order_email(order):
    """
    Send new order notification email to admin.
    Called when a new order is created.
    """
    return send_admin_order_notification_email(order, event_type='created')


def send_admin_payment_notification_email(order):
    """
    Send payment received notification email to admin.
    Called when order payment is received.
    """
    return send_admin_order_notification_email(order, event_type='paid')


def send_admin_shipped_notification_email(order):
    """
    Send order shipped notification email to admin.
    Called when order is marked as shipped.
    """
    return send_admin_order_notification_email(order, event_type='shipped')


def send_admin_delivered_notification_email(order):
    """
    Send order delivered notification email to admin.
    Called when order is marked as delivered.
    """
    return send_admin_order_notification_email(order, event_type='delivered')


def send_admin_cancelled_notification_email(order):
    """
    Send order cancelled notification email to admin.
    Called when order is cancelled.
    """
    return send_admin_order_notification_email(order, event_type='cancelled')

