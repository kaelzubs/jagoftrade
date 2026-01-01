# catalog/management/commands/fetch_products.py
from django.core.management.base import BaseCommand
from catalog.paapi_populator import ProductPopulator
from catalog.models import Product
import logging
from catalog.paapi_service_v2 import AmazonPAAPIService # pyright: ignore[reportMissingImports]
from catalog.paapi_populator import ProductPopulator
from catalog.models import Product  # Django model

# Configure logging once
logging.basicConfig(
    filename="C:\\var\\log\\fetch_products.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class Command(BaseCommand):
    help = "Fetch products from Amazon PAAPI"

    def add_arguments(self, parser):
        parser.add_argument("keyword", type=str)

    def handle(self, *args, **options):
        populator = ProductPopulator(
            paapi_service=AmazonPAAPIService()
        )
        products = populator.paapi.search_products(options["keyword"], limit=10)

        for item in products:
            Product.objects.update_or_create(
                asin=item.get("asin"),
                defaults={
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "price": item.get("price"),
                    "image_url": item.get("image_url"),
                    "affiliate_link": item.get("affiliate_link"),
                }
            )
        self.stdout.write(self.style.SUCCESS("Products fetched successfully"))

def run_fetch(keyword="laptop", limit=5):
    service = AmazonPAAPIService()
    populator = ProductPopulator(service)

    try:
        results = populator.fetch_with_backoff(keyword, limit=limit)
        for product in results:
            summary = populator.get_summary(product)
            logging.info(summary)

            # Save to DB
            Product.objects.update_or_create(
                asin=product.get("asin"),
                defaults={
                    "title": product.get("title"),
                    "description": product.get("description", ""),
                    "price": product.get("price", ""),
                    "image_url": product.get("image_url", ""),
                    "affiliate_link": product.get("affiliate_link", ""),
                }
            )
    except Exception as e:
        logging.error("Fetch failed: %s", e, exc_info=True)