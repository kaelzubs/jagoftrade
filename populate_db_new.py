#!/usr/bin/env python
"""
Database Population Script - Standalone
Populates categories and products from Amazon PAAPI
Usage: python populate_db.py [--limit=10] [--force]
"""

import os
import sys
import django
import logging
from decimal import Decimal
from io import BytesIO
from urllib.request import urlopen
from typing import Dict, List, Optional

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from django.core.files.base import ContentFile
from PIL import Image
from catalog.models import Category, Product, ProductImage
from catalog.paapi_service_v2 import AmazonPAAPIService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabasePopulator:
    def __init__(self, force=False, limit=10):
        self.force = force
        self.limit = limit
        self.paapi = None
        self.stats = {
            'categories': 0,
            'products': 0,
            'images': 0,
            'errors': 0,
        }
    
    def initialize_paapi(self):
        try:
            self.paapi = AmazonPAAPIService()
            print('✓ PAAPI initialized')
            return True
        except Exception as e:
            print(f'✗ PAAPI Error: {str(e)}')
            return False
    
    def download_image(self, url: str, timeout=10):
        if not url:
            return None
        try:
            response = urlopen(url, timeout=timeout)
            img = Image.open(BytesIO(response.read()))
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG', quality=85)
            img_bytes.seek(0)
            return ContentFile(img_bytes.getvalue())
        except Exception as e:
            logging.warning(f'Image download failed: {str(e)}')
            return None
    
    def save_product_image(self, product: Product, image_url: str, asin: str) -> bool:
        try:
            image_file = self.download_image(image_url)
            if not image_file:
                return False
            product_image = ProductImage(product=product, image=image_file)
            product_image.image.name = f'{asin}_image.jpg'
            product_image.save()
            self.stats['images'] += 1
            return True
        except Exception as e:
            logging.warning(f'Image save failed: {str(e)}')
            return False
    
    def populate_category(self, category_data: Dict):
        category_name = category_data['name']
        search_term = category_data['search_term']
        
        try:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'amazon_id': f'cat_{category_name.lower().replace(" ", "_")}'}
            )
            if created:
                self.stats['categories'] += 1
                print(f'✓ Created: {category_name}')
            else:
                print(f'  Exists: {category_name}')
            
            if self.force or category.products.count() == 0:
                self.populate_products(category, search_term)
        
        except Exception as e:
            print(f'✗ Category error: {str(e)}')
            self.stats['errors'] += 1
    
    def populate_products(self, category: Category, search_term: str):
        if not self.paapi:
            return
        
        try:
            products_list = self.paapi.search_products(search_term, limit=self.limit)
            print(f'  → Found {len(products_list)} products')
            
            for product_data in products_list:
                try:
                    asin = product_data.get('asin')
                    if not asin:
                        continue
                    
                    product, created = Product.objects.get_or_create(
                        asin=asin,
                        defaults={
                            'category': category,
                            'title': product_data.get('title', 'Unknown'),
                            'description': product_data.get('description', ''),
                            'price': Decimal(str(product_data.get('price', '0'))),
                            'affiliate_link': product_data.get('affiliate_link', ''),
                        }
                    )
                    
                    if created:
                        self.stats['products'] += 1
                        print(f'    ✓ {product.title[:45]}')
                        
                        image_url = product_data.get('image_url')
                        if image_url:
                            self.save_product_image(product, image_url, asin)
                
                except Exception as e:
                    logging.error(f'Product error: {str(e)}')
                    self.stats['errors'] += 1
        
        except Exception as e:
            logging.error(f'Search error: {str(e)}')
            self.stats['errors'] += 1
    
    def run(self):
        print('\n' + '='*70)
        print('DATABASE POPULATION - Amazon PAAPI')
        print('='*70 + '\n')
        
        if not self.initialize_paapi():
            return False
        
        categories = [
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
        
        for cat in categories:
            self.populate_category(cat)
        
        print('\n' + '='*70)
        print('SUMMARY')
        print('='*70)
        print(f'Categories: {self.stats["categories"]}')
        print(f'Products:   {self.stats["products"]}')
        print(f'Images:     {self.stats["images"]}')
        print(f'Errors:     {self.stats["errors"]}')
        print('='*70 + '\n')
        
        return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Populate database')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    
    populator = DatabasePopulator(force=args.force, limit=args.limit)
    success = populator.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
