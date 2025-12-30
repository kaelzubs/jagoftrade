#!/usr/bin/env python
"""
Database population script with sample images and mock data.
Usage: python populate_db.py [--force]
"""
import os, sys, django, logging
from decimal import Decimal
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from django.core.files.base import ContentFile
from PIL import Image
from catalog.models import Category, Product, ProductImage, CategoryImage

logging.basicConfig(level=logging.INFO)

SAMPLE_DATA = {
    'Board Games': {
        'amazon_id': 'board_games',
        'products': [
            {
                'asin': 'B000BJCDMC',
                'title': 'Catan Board Game',
                'description': 'A strategic board game where players build settlements and trade resources.',
                'price': '44.99',
                'affiliate_link': 'https://amazon.com/dp/B000BJCDMC'
            },
            {
                'asin': 'B00U26V4VQ',
                'title': 'Ticket to Ride Board Game',
                'description': 'Players compete to build railway routes across the country.',
                'price': '48.99',
                'affiliate_link': 'https://amazon.com/dp/B00U26V4VQ'
            },
            {
                'asin': 'B001OM6F0W',
                'title': 'Pandemic Board Game',
                'description': 'Cooperative board game where players work together to save the world.',
                'price': '49.99',
                'affiliate_link': 'https://amazon.com/dp/B001OM6F0W'
            },
        ]
    },
    'Video Games': {
        'amazon_id': 'video_games',
        'products': [
            {
                'asin': 'B08H95YGV6',
                'title': 'Elden Ring',
                'description': 'Open-world action RPG with challenging gameplay.',
                'price': '59.99',
                'affiliate_link': 'https://amazon.com/dp/B08H95YGV6'
            },
            {
                'asin': 'B0BGHC144Z',
                'title': 'The Legend of Zelda: Tears of the Kingdom',
                'description': 'Epic adventure game on Nintendo Switch.',
                'price': '69.99',
                'affiliate_link': 'https://amazon.com/dp/B0BGHC144Z'
            },
        ]
    },
    'Trading Cards': {
        'amazon_id': 'trading_cards',
        'products': [
            {
                'asin': 'B09RQKQHVF',
                'title': 'Pokemon TCG Booster Box',
                'description': 'Official Pokemon trading card booster box.',
                'price': '119.99',
                'affiliate_link': 'https://amazon.com/dp/B09RQKQHVF'
            },
            {
                'asin': 'B0B2HPZZ3X',
                'title': 'Magic The Gathering Booster Pack',
                'description': 'Random booster pack from MTG expansion.',
                'price': '4.99',
                'affiliate_link': 'https://amazon.com/dp/B0B2HPZZ3X'
            },
        ]
    },
    'Puzzles': {
        'amazon_id': 'puzzles',
        'products': [
            {
                'asin': 'B00LBQSFLA',
                'title': '1000-Piece Puzzle - Mountain Landscape',
                'description': 'Beautiful scenic puzzle for relaxation.',
                'price': '14.99',
                'affiliate_link': 'https://amazon.com/dp/B00LBQSFLA'
            },
        ]
    },
    'Hobby Models': {
        'amazon_id': 'hobby_models',
        'products': [
            {
                'asin': 'B08ZQBZM3C',
                'title': 'Gundam Model Kit',
                'description': 'Highly detailed plastic model kit.',
                'price': '34.99',
                'affiliate_link': 'https://amazon.com/dp/B08ZQBZM3C'
            },
        ]
    },
    'Dice & Tokens': {
        'amazon_id': 'dice_tokens',
        'products': [
            {
                'asin': 'B01C0XFOIO',
                'title': 'Polyhedral Dice Set 7-Piece',
                'description': 'Premium dice set for tabletop gaming.',
                'price': '12.99',
                'affiliate_link': 'https://amazon.com/dp/B01C0XFOIO'
            },
        ]
    },
    'Game Accessories': {
        'amazon_id': 'game_accessories',
        'products': [
            {
                'asin': 'B07YGQM5V6',
                'title': 'Deck Box for Trading Cards',
                'description': 'Protective storage for card collections.',
                'price': '8.99',
                'affiliate_link': 'https://amazon.com/dp/B07YGQM5V6'
            },
        ]
    },
    'Miniatures': {
        'amazon_id': 'miniatures',
        'products': [
            {
                'asin': 'B01F4SKQVW',
                'title': 'Fantasy Miniatures Set',
                'description': 'Detailed fantasy character miniatures.',
                'price': '24.99',
                'affiliate_link': 'https://amazon.com/dp/B01F4SKQVW'
            },
        ]
    },
    'RPG Books': {
        'amazon_id': 'rpg_books',
        'products': [
            {
                'asin': 'B0BMNQBB5Y',
                'title': 'Dungeons & Dragons Player Handbook',
                'description': 'Official D&D 5e rulebook.',
                'price': '49.99',
                'affiliate_link': 'https://amazon.com/dp/B0BMNQBB5Y'
            },
        ]
    },
    'Gaming Tables': {
        'amazon_id': 'gaming_tables',
        'products': [
            {
                'asin': 'B082SJQWTM',
                'title': 'Portable Gaming Table',
                'description': 'Folding table for tabletop gaming.',
                'price': '199.99',
                'affiliate_link': 'https://amazon.com/dp/B082SJQWTM'
            },
        ]
    },
}

def create_sample_image(color=(100, 150, 200), size=(400, 300)):
    """Create a sample image with PIL"""
    try:
        img = Image.new('RGB', size, color=color)
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        return ContentFile(img_bytes.getvalue())
    except Exception as e:
        logging.warning(f'Failed to create sample image: {str(e)}')
        return None

class DatabasePopulator:
    def __init__(self, force=False):
        self.force = force
        self.stats = {'categories': 0, 'products': 0, 'images': 0, 'errors': 0}
    
    def populate_all(self):
        print('\n' + '='*70)
        print('DATABASE POPULATION - Mock Data with Sample Images')
        print('='*70 + '\n')
        
        for category_name, category_data in SAMPLE_DATA.items():
            try:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'amazon_id': category_data['amazon_id']}
                )
                
                if created:
                    self.stats['categories'] += 1
                    print(f'✓ Created category: {category_name}')
                    
                    if self.add_category_image(category, category_name):
                        self.stats['images'] += 1
                else:
                    if self.force:
                        print(f'  Updating: {category_name}')
                    else:
                        print(f'  Exists: {category_name}')
                
                if self.force or category.products.count() == 0:
                    for product_data in category_data['products']:
                        if self.add_product(category, product_data):
                            self.stats['products'] += 1
                            
                            if self.add_product_image(product_data['asin']):
                                self.stats['images'] += 1
                
            except Exception as e:
                print(f'✗ Error with {category_name}: {str(e)}')
                self.stats['errors'] += 1
                logging.error(f'Category error: {str(e)}')
        
        self.print_summary()
        return True
    
    def add_category_image(self, category, category_name):
        """Add sample image to category"""
        try:
            colors = {
                'Board Games': (200, 100, 100),
                'Video Games': (100, 100, 200),
                'Trading Cards': (100, 200, 100),
                'Puzzles': (200, 200, 100),
                'Hobby Models': (200, 100, 200),
                'Dice & Tokens': (100, 200, 200),
                'Game Accessories': (150, 150, 100),
                'Miniatures': (150, 100, 150),
                'RPG Books': (100, 150, 150),
                'Gaming Tables': (180, 120, 100),
            }
            
            color = colors.get(category_name, (150, 150, 150))
            image_file = create_sample_image(color=color)
            
            if image_file:
                cat_image = CategoryImage(category=category, image=image_file)
                cat_image.image.name = f'{category.slug}_image.jpg'
                cat_image.save()
                print(f'  ✓ Added category image')
                return True
        except Exception as e:
            logging.warning(f'Failed to add category image: {str(e)}')
        return False
    
    def add_product(self, category, product_data):
        """Add product to database"""
        try:
            asin = product_data['asin']
            product, created = Product.objects.get_or_create(
                asin=asin,
                defaults={
                    'category': category,
                    'title': product_data['title'],
                    'description': product_data['description'],
                    'price': Decimal(product_data['price']),
                    'affiliate_link': product_data['affiliate_link'],
                }
            )
            
            if created:
                print(f'  ✓ Added product: {product.title[:50]}')
                return True
            else:
                if self.force:
                    print(f'    Updated: {product.title[:50]}')
                return False
                
        except Exception as e:
            logging.error(f'Product error: {str(e)}')
            self.stats['errors'] += 1
            return False
    
    def add_product_image(self, asin):
        """Add sample image to product"""
        try:
            product = Product.objects.get(asin=asin)
            
            if product.images.exists() and not self.force:
                return False
            
            image_file = create_sample_image(color=(120, 160, 200))
            
            if image_file:
                product_image = ProductImage(product=product, image=image_file)
                product_image.image.name = f'{asin}_image.jpg'
                product_image.save()
                return True
        except Exception as e:
            logging.warning(f'Failed to add product image for {asin}: {str(e)}')
        return False
    
    def print_summary(self):
        print('\n' + '='*70)
        print('POPULATION SUMMARY')
        print('='*70)
        print(f'Categories: {self.stats["categories"]}')
        print(f'Products:   {self.stats["products"]}')
        print(f'Images:     {self.stats["images"]}')
        print(f'Errors:     {self.stats["errors"]}')
        print('='*70 + '\n')

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Populate database with sample data and images')
    parser.add_argument('--force', action='store_true', help='Force update existing data')
    args = parser.parse_args()
    
    populator = DatabasePopulator(force=args.force)
    success = populator.populate_all()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
