"""
PAAPI Integration utilities for populating categories and products
"""

import logging
import os
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from io import BytesIO
from urllib.request import urlopen
from urllib.error import URLError

from django.core.files.base import ContentFile
from PIL import Image

from catalog.models import Category, Product, ProductImage, CategoryImage

logger = logging.getLogger(__name__)

class ProductPopulator:
    """Handle populating products from PAAPI"""
    
    DEFAULT_CATEGORIES = [
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
    
    def __init__(self, paapi_service=None):
        """Initialize with optional PAAPI service"""
        self.paapi = paapi_service
        if not self.paapi:
            # Try SimplePAAPIService first (no external dependencies)
            try:
                from catalog.simple_paapi_service import SimplePAAPIService
                self.paapi = SimplePAAPIService()
            except (ImportError, ValueError):
                # Fall back to full PAAPI service
                try:
                    from catalog.paapi_service_v2 import AmazonPAAPIService
                    self.paapi = AmazonPAAPIService()
                except (ImportError, ValueError) as e:
                    logger.error(f"Failed to initialize PAAPI service: {str(e)}")
                    self.paapi = None
    
    def populate_all_categories(self, limit: int = 10, force: bool = False) -> Dict:
        """Populate all default categories with products"""
        return self.populate_categories(self.DEFAULT_CATEGORIES, limit=limit, force=force)
    
    def populate_categories(
        self, 
        categories: List[Dict], 
        limit: int = 10, 
        force: bool = False
    ) -> Dict:
        """
        Populate specified categories with products from PAAPI
        
        Args:
            categories: List of dicts with 'name' and 'search_term' keys
            limit: Max products per category
            force: Re-populate existing products
        
        Returns:
            Dict with statistics
        """
        if not self.paapi:
            logger.error("PAAPI service not initialized")
            return {'success': False, 'error': 'PAAPI service not initialized'}
        
        stats = {
            'categories_created': 0,
            'categories_existing': 0,
            'products_created': 0,
            'products_existing': 0,
            'images_saved': 0,
            'errors': [],
        }
        
        for cat_data in categories:
            category_name = cat_data.get('name')
            search_term = cat_data.get('search_term')
            
            if not category_name or not search_term:
                stats['errors'].append(f"Invalid category data: {cat_data}")
                continue
            
            try:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'amazon_id': f'cat_{category_name.lower().replace(" ", "_")}'}
                )
                
                if created:
                    stats['categories_created'] += 1
                    logger.info(f"Created category: {category_name}")
                else:
                    stats['categories_existing'] += 1
                    logger.info(f"Category exists: {category_name}")
                
                # Fetch and populate products
                try:
                    products = self.paapi.search_products(search_term, limit=limit)
                    logger.info(f"Found {len(products)} products for '{category_name}'")
                    
                    for product_data in products:
                        created = self._create_product(category, product_data, force)
                        if created:
                            stats['products_created'] += 1
                        else:
                            stats['products_existing'] += 1
                        
                        # Try to save image
                        if self._save_product_image(product_data):
                            stats['images_saved'] += 1
                
                except Exception as e:
                    error_msg = f"Error fetching products for {category_name}: {str(e)}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            except Exception as e:
                error_msg = f"Error creating category {category_name}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        stats['success'] = True
        return stats
    
    def _create_product(self, category: Category, product_data: Dict, force: bool = False) -> bool:
        """Create a product. Returns True if created, False if exists."""
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
                logger.info(f"  Created product: {product.title}")
            
            return created
        
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            return False
    
    def _save_product_image(self, product_data: Dict) -> bool:
        """Download and save product image. Returns True if successful."""
        try:
            asin = product_data.get('asin')
            image_url = product_data.get('image_url')
            
            if not asin or not image_url:
                return False
            
            # Check if product exists and already has images
            try:
                product = Product.objects.get(asin=asin)
            except Product.DoesNotExist:
                return False
            
            if product.images.exists():
                return False
            
            # Download image
            image_data = self._download_image(image_url)
            if not image_data:
                return False
            
            # Process and save
            img_file = self._process_image(image_data)
            if not img_file:
                return False
            
            product_image = ProductImage(product=product)
            product_image.image.save(f'{asin}.jpg', img_file, save=True)
            logger.info(f"    Saved image for {product.title}")
            
            return True
        
        except Exception as e:
            logger.warning(f"Error saving product image: {str(e)}")
            return False
    
    @staticmethod
    def _download_image(url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            with urlopen(url, timeout=10) as response:
                return response.read()
        except (URLError, Exception) as e:
            logger.warning(f"Failed to download image from {url}: {str(e)}")
            return None
    
    @staticmethod
    def _process_image(image_data: bytes) -> Optional[ContentFile]:
        """Process image data and return ContentFile"""
        try:
            img = Image.open(BytesIO(image_data))
            
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            # Resize
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            return ContentFile(output.read())
        
        except Exception as e:
            logger.warning(f"Error processing image: {str(e)}")
            return None
    
    def get_summary(self) -> Dict:
        """Get current database summary"""
        return {
            'total_categories': Category.objects.count(),
            'total_products': Product.objects.count(),
            'products_with_images': Product.objects.filter(
                images__isnull=False
            ).distinct().count(),
        }
