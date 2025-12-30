"""
Django Management Command: populate_paapi
Usage: python manage.py populate_paapi
"""

import logging
import os
from decimal import Decimal
from typing import Dict, List, Optional
from io import BytesIO
from urllib.request import urlopen

from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from PIL import Image

from catalog.models import Category, Product, ProductImage

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populate categories and products from Amazon PAAPI'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Populate specific category by name',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of products per category (default: 10)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force repopulation of existing products',
        )
    
    def handle(self, *args, **options):
        try:
            from catalog.paapi_service_v2 import AmazonPAAPIService
        except ImportError:
            raise CommandError('paapi_service_v2.py not found')
        
        try:
            paapi = AmazonPAAPIService()
        except ValueError as e:
            raise CommandError(f'PAAPI Configuration Error: {str(e)}')
        
        limit = options.get('limit', 10)
        force = options.get('force', False)
        specific_category = options.get('category')
        
        categories_to_populate = [
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
        
        if specific_category:
            categories_to_populate = [
                c for c in categories_to_populate 
                if c['name'].lower() == specific_category.lower()
            ]
            if not categories_to_populate:
                raise CommandError(f'Category "{specific_category}" not found')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Populating Categories and Products from Amazon PAAPI'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        total_products = 0
        
        for cat_data in categories_to_populate:
            category_name = cat_data['name']
            search_term = cat_data['search_term']
            
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'amazon_id': f'cat_{category_name.lower().replace(" ", "_")}'}
            )
            
            status = "Created" if created else "Exists"
            self.stdout.write(f'{status}: {category_name}')
            
            try:
                products = paapi.search_products(search_term, limit=limit)
                self.stdout.write(f'  → Found {len(products)} products')
                
                for product_data in products:
                    if self._populate_product(category, product_data, paapi, force):
                        total_products += 1
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  → Error: {str(e)}'))
        
        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total categories: {Category.objects.count()}')
        self.stdout.write(f'Total products: {Product.objects.count()}')
        with_images = Product.objects.filter(images__isnull=False).distinct().count()
        self.stdout.write(f'Products with images: {with_images}')
        self.stdout.write('='*60 + '\n')
        
        self.stdout.write(self.style.SUCCESS('✓ Population complete!'))
    
    def _populate_product(self, category: Category, product_data: Dict, paapi, force: bool = False) -> bool:
        """Create or update a product. Returns True if created."""
        try:
            asin = product_data.get('asin')
            if not asin:
                return False
            
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
                self.stdout.write(f'    ✓ {product.title}')
                
                # Try to download and save image
                image_url = product_data.get('image_url')
                if image_url:
                    self._download_and_save_image(product, image_url, asin)
            
            return created
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error: {str(e)}'))
            return False
    
    def _download_and_save_image(self, product: Product, image_url: str, asin: str):
        """Download image and save to product"""
        try:
            with urlopen(image_url) as response:
                image_data = response.read()
            
            if not image_data:
                return
            
            img = Image.open(BytesIO(image_data))
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            product_image = ProductImage(product=product)
            product_image.image.save(f'{asin}.jpg', ContentFile(output.read()), save=True)
            
            self.stdout.write(f'      → Image saved')
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'      ⚠ Image failed: {str(e)[:50]}'))
