"""
Mock product population script for testing without PAAPI credentials.
Uses hardcoded test data to populate categories and products.
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from catalog.models import Category, Product

# Mock data
MOCK_CATEGORIES = [
    {'name': 'Board Games', 'amazon_id': 'BGM001'},
    {'name': 'Card Games', 'amazon_id': 'CGM002'},
    {'name': 'Video Games', 'amazon_id': 'VGM003'},
    {'name': 'Puzzles', 'amazon_id': 'PZL004'},
    {'name': 'Toys', 'amazon_id': 'TOY005'},
    {'name': 'Outdoor Games', 'amazon_id': 'OGM006'},
    {'name': 'Educational Toys', 'amazon_id': 'EDT007'},
    {'name': 'Party Games', 'amazon_id': 'PTY008'},
    {'name': 'Strategy Games', 'amazon_id': 'STR009'},
    {'name': 'Family Games', 'amazon_id': 'FAM010'},
]

MOCK_PRODUCTS = {
    'Board Games': [
        {'title': 'Catan - Strategy Board Game', 'asin': 'ASIN_CATAN', 'price': 39.99},
        {'title': 'Ticket to Ride - Railway Board Game', 'asin': 'ASIN_TTR', 'price': 44.99},
        {'title': 'Carcassonne - Tile Placement Game', 'asin': 'ASIN_CARC', 'price': 29.99},
        {'title': 'Splendor - Gem Trading Game', 'asin': 'ASIN_SPLENDOR', 'price': 34.99},
    ],
    'Card Games': [
        {'title': 'Magic: The Gathering Starter Set', 'asin': 'ASIN_MTG', 'price': 59.99},
        {'title': 'Uno Card Game', 'asin': 'ASIN_UNO', 'price': 7.99},
        {'title': 'Poker Card Set Professional', 'asin': 'ASIN_POKER', 'price': 24.99},
    ],
    'Video Games': [
        {'title': 'Nintendo Switch Sports', 'asin': 'ASIN_NSW', 'price': 49.99},
        {'title': 'PlayStation 5 Game Bundle', 'asin': 'ASIN_PS5', 'price': 59.99},
    ],
    'Puzzles': [
        {'title': '1000 Piece Landscape Puzzle', 'asin': 'ASIN_PZ1000', 'price': 14.99},
        {'title': '3D Castle Puzzle Model', 'asin': 'ASIN_3D_CASTLE', 'price': 29.99},
    ],
    'Toys': [
        {'title': 'LEGO City Police Station', 'asin': 'ASIN_LEGO_POLICE', 'price': 89.99},
        {'title': 'Remote Control Car', 'asin': 'ASIN_RC_CAR', 'price': 34.99},
    ],
    'Outdoor Games': [
        {'title': 'Badminton Set Professional', 'asin': 'ASIN_BADMINTON', 'price': 44.99},
        {'title': 'Cornhole Game Set', 'asin': 'ASIN_CORNHOLE', 'price': 54.99},
    ],
    'Educational Toys': [
        {'title': 'STEM Learning Robot Kit', 'asin': 'ASIN_STEM_ROBOT', 'price': 79.99},
        {'title': 'Coding Board Game for Kids', 'asin': 'ASIN_CODE_GAME', 'price': 29.99},
    ],
    'Party Games': [
        {'title': 'Codenames Party Game', 'asin': 'ASIN_CODENAMES', 'price': 14.99},
        {'title': 'Jackbox Party Pack 8', 'asin': 'ASIN_JACKBOX', 'price': 29.99},
    ],
    'Strategy Games': [
        {'title': 'Risk - Global Domination', 'asin': 'ASIN_RISK', 'price': 24.99},
        {'title': 'Agricola - Worker Placement', 'asin': 'ASIN_AGRICOLA', 'price': 39.99},
    ],
    'Family Games': [
        {'title': 'Monopoly Classic Edition', 'asin': 'ASIN_MONOPOLY', 'price': 19.99},
        {'title': 'Sorry! Board Game', 'asin': 'ASIN_SORRY', 'price': 12.99},
    ],
}

def populate_categories():
    """Create mock categories"""
    print("Creating categories...")
    for cat_data in MOCK_CATEGORIES:
        category, created = Category.objects.get_or_create(
            amazon_id=cat_data['amazon_id'],
            defaults={'name': cat_data['name']}
        )
        if created:
            print(f"  ✓ Created: {category.name}")
        else:
            print(f"  → Already exists: {category.name}")
    
    print(f"✓ {Category.objects.count()} categories in database\n")

def populate_products():
    """Create mock products for each category"""
    print("Creating products...")
    for category_name, products in MOCK_PRODUCTS.items():
        try:
            category = Category.objects.get(name=category_name)
            for prod_data in products:
                product, created = Product.objects.get_or_create(
                    asin=prod_data['asin'],
                    defaults={
                        'category': category,
                        'title': prod_data['title'],
                        'price': Decimal(str(prod_data['price'])),
                        'description': f"Mock product for testing: {prod_data['title']}",
                        'affiliate_link': f"https://amazon.com/dp/{prod_data['asin']}"
                    }
                )
                if created:
                    print(f"  ✓ {category_name}: {product.title}")
                else:
                    print(f"  → {category_name}: {product.title} (exists)")
        except Category.DoesNotExist:
            print(f"  ✗ Category not found: {category_name}")
    
    print(f"✓ {Product.objects.count()} products in database\n")

def main():
    """Main population function"""
    print("=" * 60)
    print("Mock Product Population Script")
    print("=" * 60 + "\n")
    
    # Clear existing data (optional)
    clear_data = input("Clear existing data first? (y/n): ").strip().lower() == 'y'
    if clear_data:
        print("Clearing existing data...")
        Product.objects.all().delete()
        Category.objects.all().delete()
        print("✓ Cleared\n")
    
    # Populate
    populate_categories()
    populate_products()
    
    # Summary
    print("=" * 60)
    print("Population Complete!")
    print(f"Categories: {Category.objects.count()}")
    print(f"Products: {Product.objects.count()}")
    print("=" * 60)

if __name__ == '__main__':
    main()
