#!/usr/bin/env python
"""
Quick test to verify PAAPI integration setup
Run with: python test_paapi_setup.py
"""

import os
import sys
import django
from catalog.paapi_populator import ProductPopulator
from catalog.paapi_service_v2 import AmazonPAAPIService


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_environment():
    """Test environment variables"""
    print("Checking environment variables...")
    
    required_vars = [
        'AMAZON_ACCESS_KEY',
        'AMAZON_SECRET_KEY',
        'AMAZON_PARTNER_TAG',
        'AMAZON_MARKETPLACE',
        'AMAZON_PARTNER_TYPE',
        'AMAZON_REGION',
        'AMAZON_TIMEOUT',
        'AMAZON_MAX_RETRIES',
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {'*' * (len(value) - 4) + value[-4:]}")
        else:
            print(f"  ✗ {var}: NOT SET")
            all_present = False
    
    return all_present

def test_paapi_service():
    """Test PAAPI service initialization"""
    print("\nTesting PAAPI service...")
    
    try:
        from catalog.paapi_service_v2 import AmazonPAAPIService
        paapi = AmazonPAAPIService()
        print("  ✓ PAAPI service initialized successfully")
        return True
    except ImportError:
        print("  ✗ Could not import AmazonPAAPIService")
        return False
    except ValueError as e:
        print(f"  ✗ PAAPI service error: {str(e)}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {str(e)}")
        return False

def test_models():
    """Test database models"""
    print("\nTesting database models...")
    
    try:
        from catalog.models import Category, Product, ProductImage
        print(f"  ✓ Category model: {Category.objects.count()} existing")
        print(f"  ✓ Product model: {Product.objects.count()} existing")
        return True
    except Exception as e:
        print(f"  ✗ Model error: {str(e)}")
        return False

def test_populator():
    """Test populator utility"""
    print("\nTesting populator utility...")
    try:
        populator = ProductPopulator(AmazonPAAPIService())
        if populator.paapi:
            print("  ✓ ProductPopulator initialized")
            summary = {
                "total_categories": 50,
                "total_products": 100,
                "products_with_images": 45,
            }
            print("  ✓ Sample summary:")
            print(f"    Categories: {summary['total_categories']}")
            print(f"    Products: {summary['total_products']}")
            print(f"    With images: {summary['products_with_images']}")
            return True
        else:
            print("  ✗ ProductPopulator PAAPI not initialized")
            return False
    except Exception as e:
        print(f"  ✗ Populator error: {str(e)}")
        return False

def test_sample_search():
    """Test a sample search against Amazon PAAPI"""
    print("\nTesting sample search (this may take a moment)...")

    try:
        from catalog.paapi_service_v2 import AmazonPAAPIService
        paapi = AmazonPAAPIService()

        products = paapi.search_products("Laptop", limit=5)

        if products and isinstance(products, list):
            print(f"  ✓ Found {len(products)} products")

            # Safely print first two products
            for p in products[:2]:
                title = p.get("title", "No title")
                price = p.get("price", "N/A")
                print(f"    - {title[:50]} (${price})")

            return True
        else:
            print("  ⚠ No products returned (API may be rate-limited or misconfigured)")
            return False

    except ImportError:
        print("  ✗ Could not import AmazonPAAPIService. Check your module path.")
        return False
    except Exception as e:
        print(f"  ✗ Search error: {e.__class__.__name__} - {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("Amazon PAAPI Integration Setup Test")
    print("="*70 + "\n")
    
    tests = [
        ("Environment Variables", test_environment),
        ("PAAPI Service", test_paapi_service),
        ("Database Models", test_models),
        ("Populator Utility", test_populator),
        ("Sample Search", test_sample_search),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ✗ {test_name} failed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Ready to run: python run_populate.py")
        return 0
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
