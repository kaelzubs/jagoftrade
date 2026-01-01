#!/usr/bin/env python
import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalog.models import Category, Product, ProductImage
from catalog.paapi_service_v2 import AmazonPAAPIService
from catalog.utils.images import fetch_and_prepare_image

logger = logging.getLogger(__name__)


DEFAULT_CATEGORIES: List[Dict[str, str]] = [
    {"name": "Board Games", "search_term": "board games"},
    {"name": "Video Games", "search_term": "video games"},
    {"name": "Trading Cards", "search_term": "trading card games"},
    {"name": "Puzzles", "search_term": "puzzles"},
    {"name": "Hobby Models", "search_term": "hobby models"},
    {"name": "Dice & Tokens", "search_term": "dice tokens"},
    {"name": "Game Accessories", "search_term": "board game accessories"},
    {"name": "Miniatures", "search_term": "miniatures"},
    {"name": "RPG Books", "search_term": "rpg books"},
    {"name": "Gaming Tables", "search_term": "gaming tables"},
]


class CatalogPopulator:
    def __init__(
        self,
        force: bool = False,
        limit: int = 10,
        dry_run: bool = False,
        rate_limit: float = 0.0,
    ):
        self.force = force
        self.limit = limit
        self.dry_run = dry_run
        self.rate_limit = rate_limit

        self.paapi: Optional[AmazonPAAPIService] = None
        self.stats = {"categories": 0, "products": 0, "images": 0, "errors": 0}

    def initialize_paapi(self) -> bool:
        try:
            self.paapi = AmazonPAAPIService()
            logger.info("PAAPI initialized")
            return True
        except Exception as exc:
            logger.error("PAAPI initialization failed: %s", exc, exc_info=True)
            self.stats["errors"] += 1
            return False

    def save_product_image(self, product: Product, image_url: str, asin: str) -> bool:
        if not image_url:
            return False

        try:
            if self.dry_run:
                logger.debug("[dry-run] Would download image: %s", image_url)
                return True

            content_file, filename = fetch_and_prepare_image(image_url, asin=asin)
            if not content_file:
                logger.warning("Image rejected or failed: %s", image_url)
                return False

            product_image = ProductImage(product=product, image=content_file)
            product_image.image.name = filename
            product_image.save()
            self.stats["images"] += 1
            logger.info("Saved image for %s: %s", asin, filename)
            return True
        except Exception as exc:
            logger.warning("Image save failed for %s: %s", asin, exc, exc_info=True)
            self.stats["errors"] += 1
            return False

    def populate_category(self, category_data: Dict[str, str]) -> None:
        name = category_data["name"]
        search_term = category_data["search_term"]

        try:
            amazon_id_default = f"cat_{slugify(name)}"
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={"amazon_id": amazon_id_default},
            )

            if created:
                self.stats["categories"] += 1
                logger.info("Created category: %s", name)
            else:
                logger.info("Category exists: %s", name)

            should_populate = self.force or category.products.count() == 0
            if not should_populate:
                logger.info("Skipping products for %s (already populated)", name)
                return

            self.populate_products(category, search_term)
        except Exception as exc:
            logger.error("Category error (%s): %s", name, exc, exc_info=True)
            self.stats["errors"] += 1

    def populate_products(self, category: Category, search_term: str) -> None:
        if not self.paapi:
            logger.error("PAAPI is not initialized.")
            self.stats["errors"] += 1
            return

        try:
            products_list = self.paapi.search_products(search_term, limit=self.limit)
            logger.info("Found %d products for '%s'", len(products_list), search_term)
        except Exception as exc:
            logger.error("Search error for '%s': %s", search_term, exc, exc_info=True)
            self.stats["errors"] += 1
            return

        for product_data in products_list:
            asin = product_data.get("asin")
            if not asin:
                logger.debug("Skipping product missing ASIN: %s", product_data)
                continue

            title = product_data.get("title") or "Unknown"
            description = product_data.get("description") or ""
            affiliate_link = product_data.get("affiliate_link") or ""
            image_url = product_data.get("image_url") or ""
            price_val = product_data.get("price", "0")

            # Validate price coercion
            try:
                price = Decimal(str(price_val))
                if price < Decimal("0"):
                    price = Decimal("0")
            except Exception:
                price = Decimal("0")

            try:
                if self.dry_run:
                    logger.info(
                        "[dry-run] Would create product: ASIN=%s, title=%s", asin, title
                    )
                    self.stats["products"] += 1
                else:
                    with transaction.atomic():
                        product, created = Product.objects.select_for_update().get_or_create(
                            asin=asin,
                            defaults={
                                "category": category,
                                "title": title,
                                "description": description,
                                "price": price,
                                "affiliate_link": affiliate_link,
                            },
                        )
                        if created:
                            self.stats["products"] += 1
                            logger.info("Created product: %s", title[:120])
                            if image_url:
                                self.save_product_image(product, image_url, asin)
                        else:
                            logger.info("Product exists: %s", title[:120])
                            # If force, try to update missing fields/images
                            if self.force:
                                updates = {}
                                if not product.description and description:
                                    updates["description"] = description
                                if product.price is None or product.price == Decimal("0"):
                                    updates["price"] = price
                                if updates:
                                    for k, v in updates.items():
                                        setattr(product, k, v)
                                    product.save(update_fields=list(updates.keys()))
                                    logger.info("Updated product fields for ASIN=%s", asin)
                                if image_url and not product.images.exists():
                                    self.save_product_image(product, image_url, asin)
            except Exception as exc:
                logger.error("Product error (ASIN=%s): %s", asin, exc, exc_info=True)
                self.stats["errors"] += 1

            if self.rate_limit and self.rate_limit > 0:
                time.sleep(self.rate_limit)

    def run(self, categories: List[Dict[str, str]]) -> bool:
        logger.info("=== DATABASE POPULATION - Amazon PAAPI ===")

        if not self.initialize_paapi():
            return False

        for cat in categories:
            self.populate_category(cat)

        logger.info(
            "=== SUMMARY ===\nCategories: %d\nProducts:   %d\nImages:     %d\nErrors:     %d",
            self.stats["categories"],
            self.stats["products"],
            self.stats["images"],
            self.stats["errors"],
        )
        return self.stats["errors"] == 0


class Command(BaseCommand):
    help = "Populate catalog with categories and products via Amazon PAAPI"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=10, help="Max products per category")
        parser.add_argument("--force", action="store_true", help="Re-populate existing categories/products")
        parser.add_argument("--dry-run", action="store_true", help="Simulate without writing to DB/storage")
        parser.add_argument("--rate-limit", type=float, default=1.0, help="Seconds to sleep between product operations")
        parser.add_argument(
            "--categories",
            type=str,
            help="Comma-separated list of category names to populate (defaults to built-in set)",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        force = options["force"]
        dry_run = options["dry_run"]
        rate_limit = options["rate_limit"]
        categories_arg = options.get("categories")

        if categories_arg:
            requested = [c.strip() for c in categories_arg.split(",") if c.strip()]
            selection = []
            for c in DEFAULT_CATEGORIES:
                if c["name"] in requested:
                    selection.append(c)
            if not selection:
                raise CommandError("No matching categories found for provided names.")
            categories = selection
        else:
            categories = DEFAULT_CATEGORIES

        # Configure base logging for command context if not already set
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )

        populator = CatalogPopulator(
            force=force, limit=limit, dry_run=dry_run, rate_limit=rate_limit
        )
        success = populator.run(categories)
        if not success:
            raise CommandError("Population completed with errors.")