from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from .emails import (
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
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, update_fields, **kwargs):
    """
    Signal handler to send emails when order status changes.
    Sends both customer and admin notifications.
    """
    # Send confirmation email when order is first created
    if created:
        try:
            send_order_confirmation_email(instance)
        except Exception as e:
            logger.error(f"Error sending confirmation email for order {instance.pk}: {e}")
        
        # Also notify admin of new order
        try:
            send_admin_new_order_email(instance)
        except Exception as e:
            logger.error(f"Error sending admin new order notification for order {instance.pk}: {e}")
    
    # Send emails based on status changes
    if update_fields and 'status' in update_fields:
        if instance.status == 'paid':
            try:
                send_payment_received_email(instance)
            except Exception as e:
                logger.error(f"Error sending payment email for order {instance.pk}: {e}")
            
            # Notify admin of payment
            try:
                send_admin_payment_notification_email(instance)
            except Exception as e:
                logger.error(f"Error sending admin payment notification for order {instance.pk}: {e}")
        
        elif instance.status == 'sent_to_supplier':
            try:
                send_order_shipped_email(instance)
            except Exception as e:
                logger.error(f"Error sending shipment email for order {instance.pk}: {e}")
            
            # Notify admin of shipment
            try:
                send_admin_shipped_notification_email(instance)
            except Exception as e:
                logger.error(f"Error sending admin shipment notification for order {instance.pk}: {e}")
        
        elif instance.status == 'fulfilled':
            try:
                send_order_delivered_email(instance)
            except Exception as e:
                logger.error(f"Error sending delivered email for order {instance.pk}: {e}")
            
            # Notify admin of delivery
            try:
                send_admin_delivered_notification_email(instance)
            except Exception as e:
                logger.error(f"Error sending admin delivery notification for order {instance.pk}: {e}")
        
        elif instance.status == 'cancelled':
            try:
                send_order_cancelled_email(instance)
            except Exception as e:
                logger.error(f"Error sending cancellation email for order {instance.pk}: {e}")
            
            # Notify admin of cancellation
            try:
                send_admin_cancelled_notification_email(instance)
            except Exception as e:
                logger.error(f"Error sending admin cancellation notification for order {instance.pk}: {e}")

