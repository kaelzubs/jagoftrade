import os
from typing import Dict
import logging
from catalog.paapi_service_v2 import AmazonPAAPIService
import time
import logging
from requests.exceptions import RequestException


logger = logging.getLogger(__name__)

class ProductPopulator:
    def __init__(self, paapi_service, base_rate_limit=1.0):
        self.paapi = paapi_service
        if not self.paapi:
            self.paapi = AmazonPAAPIService()
        self.stats = {"errors": 0}
        self.rate_limit = base_rate_limit  # default sleep time
        self.max_rate_limit = 30.0   
        
    def handle(self, *args, **options):
        rate_limit = options.get("rate_limit", 1.0)
        products = self.paapi.search_products(options["keyword"], limit=10)

        for product in products:
            summary = self.get_summary(product)
            print(summary)
            time.sleep(rate_limit)  # apply rate limit correctly
        
    def fetch_with_backoff(self, keyword, limit=10):
        products = []
        retries = 0

        while retries < 5:  # max retries
            try:
                items = self.paapi.search_products(keyword, limit=limit)
                if items:
                    products.extend(items)
                    # reset rate limit after success
                    self.rate_limit = 1.0
                    break
                else:
                    logger.warning("Empty response, backing off...")
                    time.sleep(self.rate_limit)
                    self.rate_limit = min(self.rate_limit * 2, self.max_rate_limit)
                    retries += 1
            except RequestException as e:
                if "429" in str(e) or "TooManyRequests" in str(e):
                    logger.warning("Throttled by API, backing off...")
                    time.sleep(self.rate_limit)
                    self.rate_limit = min(self.rate_limit * 2, self.max_rate_limit)
                else:
                    logger.error("Unexpected error: %s", e)
                    break
                retries += 1

        return products

        
    def get_summary(self, product: Dict) -> str:
        """
        Return a short summary string for a product dict.
        Expected keys: 'title', 'price', 'asin', 'affiliate_link'
        """
        title = product.get("title", "Unknown Title")
        price = product.get("price", "0")
        asin = product.get("asin", "")
        link = product.get("affiliate_link", "")

        return f"{title} ({asin}) - {int(price)} | {link}"


    def initialize_paapi(self, ) -> bool:
        """Initialize PAAPI service using environment variables."""
        try:
            # Load credentials from environment
            self.access_key = os.getenv("AMAZON_ACCESS_KEY")
            self.secret_key = os.getenv("AMAZON_SECRET_KEY")
            self.partner_tag = os.getenv("AMAZON_PARTNER_TAG")
            self.marketplace = os.getenv("AMAZON_MARKETPLACE")
            self.region = os.getenv("AMAZON_REGION", "us-east-1")
            self.max_retries = int(os.getenv("AMAZON_MAX_RETRIES", "3"))
            self.timeout = int(os.getenv("AMAZON_TIMEOUT", "10"))

            # Instantiate PAAPI service if not already provided
            if not self.paapi:
                self.paapi = AmazonPAAPIService()
                
            # Validate required credentials
            if not all([self.access_key, self.secret_key, self.partner_tag, self.marketplace, self.region, self.timeout, self.max_retries]):
                raise RuntimeError("Amazon PAAPI credentials are missing")

            logger.info("✓ PAAPI initialized successfully")
            return True

        except Exception as exc:
            logger.error("✗ PAAPI initialization failed: %s", exc, exc_info=True)
            self.stats["errors"] += 1
            return False