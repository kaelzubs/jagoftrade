import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")
django.setup()

from catalog.models import Product
from paapi.service import AmazonProductService
from decimal import Decimal
import os


def sync_amazon_product(asin):
    service = AmazonProductService(
        access_key=os.getenv('AMAZON_ACCESS_KEY'),
        secret_key=os.getenv('AMAZON_SECRET_KEY'),
        partner_tag=os.getenv('AMAZON_PARTNER_TAG')
    )
    data = service.fetch_product(asin)
    
    item = data["ItemsResult"]["Items"][0]

    Product.objects.update_or_create(
        asin=asin,
        defaults={
            "title": item["ItemInfo"]["Title"]["DisplayValue"],
            "price": item["Offers"]["Listings"][0]["Price"]["Amount"],
            "image_url": item["Images"]["Primary"]["Large"]["URL"],
            "features": "\n".join(item["ItemInfo"].get("Features", {}).get("DisplayValues", [])),
        }
    )


# def sync_amazon_product(asin):
#     service = AmazonProductService(
#         access_key=os.getenv('AMAZON_ACCESS_KEY'),
#         secret_key=os.getenv('AMAZON_SECRET_KEY'),
#         partner_tag=os.getenv('AMAZON_PARTNER_TAG')
#     )
#     data = service.fetch_product(asin)
    
#     if data is None:
#         return
    
#     Product.objects.update_or_create(
#         asin=asin,
#         defaults={
#             "title": data["title"],
#             "price": Decimal(data["price"]),
#             "currency": data["currency"],
#             "image": data["image"],
#             "features": "\n".join(data["features"])
#         }
#     )        