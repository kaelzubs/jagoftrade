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
    
def browse_node(node_id, page=1, page_size=10):
    """
    Fetches products from a specific Amazon browse node using the Product Advertising API.
    
    Args:
        node_id (str): The ID of the browse node to fetch products from.
        
    Returns:
        list: A list of product dictionaries containing details like title, ASIN, price, and affiliate link.
    """
    client = get_paapi_client()
    try:
        result = client.get_browse_nodes(browse_node_ids=[node_id], item_count=page_size, page=page)
        return result["BrowseNodesResult"]["BrowseNodes"][0]
    except AmazonApiException as e:
        print(f"Error fetching browse node with ID {node_id}: {e}")
        return []
    
    
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
        result = client.get_items(asin)
        return result["ItemsResult"]["Items"][0]  # Return the first item from the results
    except AmazonApiException as e:
        print(f"Error fetching product with ASIN {asin}: {e}")
        return None
    
    
def search_products(keywords, max_results=10, page=1):
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
        result = client.search_items(keywords=keywords, item_count=max_results, item_page=page)
        return result["SearchResult"]["Items"]
    except AmazonApiException as e:
        print(f"Error searching products with keywords '{keywords}': {e}")
        return []
    
def save_category_from_paapi(data):
    """
    Fetches category details from the Amazon Product Advertising API using the provided browse node ID
    and saves it to the database if it doesn't already exist.
    
    Args:
        node_id (str): The Amazon browse node ID to fetch and save as a category.
        parent_id (str, optional): The Amazon browse node ID of the parent category, if applicable. Defaults to None.
        
    Returns:
        Category: The saved Category instance, or None if there was an error.
    """
    node_id = data["id"]
    name = data["DisplayName"]
    parent_id = data.get("Ancestors", {}).get("Id")
    
    Category.objects.get_or_create(
        node_id=node_id,
        defaults={
            "name": name,
            "parent_id": parent_id
        },
    )
    
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
    price = data["Offers"]["Listings"][0]["Price"]["Amount"]
    amount = data["Offers"]["Listings"][0]["Price"]["Amount"]
    currency = data["Offers"]["Listings"][0]["Price"]["Currency"]
    affiliate_link = data["DetailPageURL"]
    image_url = data["Images"]["Primary"]["Medium"]["URL"]
    description = data["ItemInfo"].get("Features", {}).get("DisplayValue", "")
    brands = data["ItemInfo"].get("ByLineInfo", {}).get("Brand", {}).get("DisplayValue", "")
    
    Product.objects.get_or_create(
        title=title,
        defaults={
            "asin": asin,
            "price": price,
            "affiliate_link": affiliate_link,
            "description": description,
        },
    )