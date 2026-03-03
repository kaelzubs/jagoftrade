from celery import shared_task
from .models import Product
from .services.paapi import fetch_product, save_product_from_paapi

@shared_task
def refresh_products():
    """
    Celery task to update a product's details by fetching data from the Amazon Product Advertising API using its ASIN.
    
    Args:
        asin (str): The ASIN of the product to update. 
    Returns:
        str: A message indicating the result of the update operation.
    """
    
    for product in Product.objects.all():
        data = fetch_product(product.asin)
        if data:
            save_product_from_paapi(data)