from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Order

@csrf_exempt
def stripe_webhook(request):
    # verify signature in production
    # parse event, find PaymentIntent.succeeded, then:
    order_id = event['data']['object']['metadata']['order_id']
    order = Order.objects.get(id=order_id)
    order.status = 'paid'
    order.save()
    return HttpResponse(status=200)