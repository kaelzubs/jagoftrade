#!/usr/bin/env python
"""
Populate categories and products from Amazon PAAPI
Usage: python populate_paapi_categories_products.py
"""

import os
import sys
import django
import logging
from decimal import Decimal
from typing import Dict, List
from io import BytesIO
from urllib.request import urlopen

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from catalog.models import Category, Product, CategoryImage, ProductImage
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import PAAPI service
try:
    from catalog.paapi_service_v2 import AmazonPAAPIService
except ImportError:
    logger.error("Could not import AmazonPAAPIService. Make sure paapi_service_v2.py exists.")
    sys.exit(1)

# Default categories to populate
CATEGORIES_TO_POPULATE = [
    {'name': 'Board Games', 'search_term': 'board games'},
    {'name': 'Video Games', 'search_term': 'video games'},
    {'name': 'Trading Cards', 'search_term': 'trading card games'},
    {'name': 'Puzzles', 'search_term': 'puzzles'},
    {'name': 'Hobby Models', 'search_term': 'hobby models'},
    {'name': 'Dice & Tokens', 'search_term': 'dice tokens'},
    {'name': 'Game Accessories', 'search_term': 'board game accessories'},
    {'name': 'Miniatures', 'search_term': 'miniatures'},
    {'name': 'RPG Books', 'search_term': 'rpg books'},
    {'name': 'Gaming Tables', 'search_term': 'gaming tables'},
]

def download_image_from_url(url: str) -> bytes:
    """Download image from URL and return as bytes"""
    try:
        with urlopen(url) as response:
            return response.read()
    except Exception as e:
        logger.warning(f"Failed to download image from {url}: {str(e)}")
        return None

def save_image_to_model(image_data: bytes, filename: str) -> str:
    """Save image data and return the filename"""
    if not image_data:
        return None
    
    try:
        img = Image.open(BytesIO(image_data))
        img.thumbnail((800, 800))
        
        # Save to temporary location
        output = BytesIO()
        img.save(output, format='JPEG')
        output.seek(0)
        
        return output
    except Exception as e:
        logger.warning(f"Failed to process image: {str(e)}")
        return None

def populate_categories():
    """Create or update categories from PAAPI"""
    logger.info("Starting category population...")
    paapi = AmazonPAAPIService()
    
    for cat_data in CATEGORIES_TO_POPULATE:
        category_name = cat_data['name']
        search_term = cat_data['search_term']
        
        # Create or get category
        category, created = Category.objects.get_or_create(
            name=category_name,
            defaults={'amazon_id': f'cat_{category_name.lower().replace(" ", "_")}'}
        )
        
        status = "created" if created else "exists"
        logger.info(f"Category '{category_name}' {status}")
        
        # Fetch products for this category
        try:
            products = paapi.search_products(search_term, limit=10)
            logger.info(f"Found {len(products)} products for '{category_name}'")
            
            for product_data in products:
                populate_product(category, product_data, paapi)
        
        except Exception as e:
            logger.error(f"Error fetching products for {category_name}: {str(e)}")

def populate_product(category: Category, product_data: Dict, paapi: AmazonPAAPIService):
    """Create or update a product"""
    try:
        asin = product_data.get('asin')
        if not asin:
            return
        
        product, created = Product.objects.get_or_create(
            asin=asin,
            defaults={
                'category': category,
                'title': product_data.get('title', 'Unknown Product')[:200],
                'description': '',
                'price': Decimal(str(product_data.get('price', '0.00'))),
                'affiliate_link': product_data.get('affiliate_link', ''),
            }
        )
        
        if created:
            logger.info(f"  → Created product: {product.title}")
        
        # Download and save product image
        image_url = product_data.get('image_url')
        if image_url and not product.images.exists():
            try:
                image_data = download_image_from_url(image_url)
                if image_data:
                    img_file = save_image_to_model(image_data, f'{asin}.jpg')
                    if img_file:
                        product_image = ProductImage(product=product)
                        product_image.image.save(f'{asin}.jpg', img_file, save=True)
                        logger.info(f"    → Saved image for {product.title}")
            except Exception as e:
                logger.warning(f"    → Failed to save image: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error populating product {product_data.get('asin')}: {str(e)}")

def cleanup_old_products():
    """Remove products with no images or descriptions (incomplete data)"""
    logger.info("Cleaning up incomplete products...")
    # Keep all products for now - only delete if explicitly needed
    pass

def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("Populating Categories and Products from Amazon PAAPI")
    logger.info("=" * 60)
    
    try:
        populate_categories()
        cleanup_old_products()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total categories: {Category.objects.count()}")
        logger.info(f"Total products: {Product.objects.count()}")
        logger.info(f"Products with images: {Product.objects.filter(images__isnull=False).distinct().count()}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
