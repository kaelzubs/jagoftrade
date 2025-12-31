import os
import logging
from catalog.paapi_service_v2 import AmazonPAAPIService

logger = logging.getLogger(__name__)

class ProductPopulator:
    def __init__(self):
        self.paapi = None
        self.stats = {"errors": 0}

    def initialize_paapi(self) -> bool:
        """Initialize PAAPI service using environment variables."""
        try:
            # Load credentials from environment
            access_key = os.getenv("AMAZON_ACCESS_KEY")
            secret_key = os.getenv("AMAZON_SECRET_KEY")
            partner_tag = os.getenv("AMAZON_PARTNER_TAG")
            region = os.getenv("AMAZON_REGION", "us-east-1")
            marketplace = os.getenv('AMAZON_MARKETPLACE')
            max_retries = int(os.getenv("AMAZON_MAX_RETRIES", "3"))
            timeout = int(os.getenv("AMAZON_TIMEOUT", "10"))

            if not all([
                access_key,
                secret_key,
                partner_tag,
                region,
                marketplace,
                max_retries,
                timeout
            ]):
                raise RuntimeError("Amazon PAAPI credentials are missing")

            # Instantiate PAAPI service if not already provided
            if not self.paapi:
                self.paapi = AmazonPAAPIService(
                    access_key=access_key,
                    secret_key=secret_key,
                    partner_tag=partner_tag,
                )

            logger.info("✓ PAAPI initialized")
            return True

        except Exception as exc:
            logger.error("✗ PAAPI Error: %s", exc, exc_info=True)
            self.stats["errors"] += 1
            return False