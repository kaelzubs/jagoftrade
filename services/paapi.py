from amazon_paapi import AmazonApi, AmazonApiException
from django.conf import settings
from catalog.models import Product


def get_paapi_client():
    """
    Initializes and returns an instance of the Amazon Product Advertising API client.
    The client is configured using credentials and settings from the Django settings module.
    
    Returns:
        AmazonApi: An instance of the AmazonApi client ready for making API calls.
    """
    return AmazonApi(
        aws_access_key=settings.AWS_ACCESS_KEY_ID,
        aws_secret_key=settings.AWS_SECRET_ACCESS_KEY,
        partner_tag=settings.PARTNER_TAG,
        partner_type="Associates"
    )
    
def fetch_product(asin):
    """
    Fetches product details from the Amazon Product Advertising API using the provided ASIN.
    
    Args:
        asin (str): The ASIN of the product to fetch.
    Returns:
        dict: A dictionary containing product details such as title, price, affiliate link, and image URL.
    """
    client = get_paapi_client()
    try:
        result = client.get_items(asin=asin)
        return result["ItemsResult"]["Items"][0]  # Return the first item from the results
    except AmazonApiException as e:
        print(f"Error fetching product with ASIN {asin}: {e}")
        return None
    
    
def search_products(keywords, category=None, max_results=10):
    """
    Searches for products on Amazon using the Product Advertising API.
    
    Args:
        keywords (str): The search keywords to query products.
        category (str, optional): The category to filter products by. Defaults to None.
        max_results (int, optional): The maximum number of results to return. Defaults to 10.
        
    Returns:
        list: A list of product dictionaries containing details like title, ASIN, price, and affiliate link.
    """
    client = get_paapi_client()
    try:
        result = client.search_items(keywords=keywords, item_count=max_results, search_index=category)
        return result["SearchResult"]["Items"]
    except AmazonApiException as e:
        print(f"Error searching products with keywords '{keywords}': {e}")
        return []

    
def save_product_from_paapi(data):
    """
    Fetches product details from the Amazon Product Advertising API using the provided ASIN
    and saves it to the database if it doesn't already exist.
    
    Args:
        asin (str): The ASIN of the product to fetch and save.
        
    Returns:
        Product: The saved Product instance, or None if there was an error.
    """
    asin = data["ASIN"]
    title = data["ItemInfo"]["Title"]["DisplayValue"]
    price = data["Offers"]["Listings"][0]["Price"]["Amount"] if data.get("Offers") else None
    amount = data["Offers"]["Listings"][0]["Price"]["Amount"] if data.get("Offers") else None
    currency = data["Offers"]["Listings"][0]["Price"]["Currency"] if data.get("Offers") else None
    affiliate_link = data["DetailPageURL"]
    image_url = data["Images"]["Primary"]["Medium"]["URL"] if data.get("Images") else None
    description = data["ItemInfo"].get("Features", {}).get("DisplayValue", "")
    brands = data["ItemInfo"].get("ByLineInfo", {}).get("Brand", {}).get("DisplayValue", "")
    
    Product.objects.get_or_create(
        title=title,
        defaults={
            "asin": asin,
            "title": title,
            "price": price,
            "currency": currency,
            "amount": amount,
            "image_url": image_url,
            "brands": brands,
            "affiliate_link": affiliate_link,
            "description": description
        },
    )