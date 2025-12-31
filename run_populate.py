#!/usr/bin/env python
"""
Simple script to populate categories and products from Amazon PAAPI
Run with: python run_populate.py
"""

import os
import sys
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from catalog.paapi_populator import ProductPopulator

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    print("\n" + "="*70)
    print("Populating Categories and Products from Amazon PAAPI")
    print("="*70 + "\n")
    
    try:
        populator = ProductPopulator()
        
        if not populator.paapi:
            print("❌ Error: Could not initialize PAAPI service")
            print("   Make sure Amazon credentials are set in .env file:")
            print("   - AMAZON_ACCESS_KEY")
            print("   - AMAZON_SECRET_KEY")
            print("   - AMAZON_PARTNER_TAG")
            print("   - AMAZON_COUNTRY (optional, default: US)")
            return 1
        
        print("✓ PAAPI service initialized")
        print("\nFetching products from Amazon...\n")
        
        # Populate all categories
        stats = populator.populate_all_categories(limit=100)
        
        if not stats.get('success'):
            print(f"❌ Error: {stats.get('error')}")
            return 1
        
        # Print summary
        print("\n" + "="*70)
        print("POPULATION COMPLETE - Summary")
        print("="*70)
        print(f"✓ Categories created:    {stats['categories_created']}")
        print(f"✓ Categories existing:   {stats['categories_existing']}")
        print(f"✓ Products created:      {stats['products_created']}")
        print(f"✓ Products existing:     {stats['products_existing']}")
        print(f"✓ Images saved:          {stats['images_saved']}")
        
        if stats['errors']:
            print(f"\n⚠ Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        # Get current state
        summary = populator.get_summary()
        print("\n" + "="*70)
        print("DATABASE SUMMARY")
        print("="*70)
        print(f"Total categories: {summary['total_categories']}")
        print(f"Total products:   {summary['total_products']}")
        print(f"With images:      {summary['products_with_images']}")
        print("="*70 + "\n")
        
        return 0
    
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
