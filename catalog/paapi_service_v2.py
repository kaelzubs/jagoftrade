import os
import logging
import requests
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from requests_aws4auth import AWS4Auth
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class AmazonPAAPIService:
    """Service for interacting with Amazon Product Advertising API v5"""
    
    def __init__(self):
        self.access_key = os.getenv('AMAZON_ACCESS_KEY')
        self.secret_key = os.getenv('AMAZON_SECRET_KEY')
        self.partner_tag = os.getenv('AMAZON_PARTNER_TAG')
        self.country = os.getenv('AMAZON_COUNTRY', 'US')
        
        self.host = f'webservices.amazon.com'
        self.region = self._get_region_from_country()
        self.service = 'ProductAdvertisingAPI'
        self.endpoint = f'https://{self.host}/paapi5/getitems'
        
        if not all([self.access_key, self.secret_key, self.partner_tag]):
            raise ValueError("Missing Amazon PAAPI credentials in environment variables")
    
    def _get_region_from_country(self) -> str:
        """Map country code to AWS region"""
        country_region_map = {
            'US': 'us-east-1',
            'CA': 'us-east-1',
            'MX': 'us-east-1',
            'BR': 'us-east-1',
            'GB': 'eu-west-1',
            'FR': 'eu-west-1',
            'DE': 'eu-west-1',
            'IT': 'eu-west-1',
            'ES': 'eu-west-1',
            'JP': 'ap-northeast-1',
            'IN': 'ap-south-1',
            'AU': 'ap-southeast-2',
        }
        return country_region_map.get(self.country, 'us-east-1')
    
    def search_products(self, keywords: str, limit: int = 10) -> List[Dict]:
        """Search for products by keywords"""
        try:
            auth = AWS4Auth(
                self.access_key,
                self.secret_key,
                self.region,
                self.service
            )
            
            payload = {
                "Keywords": keywords,
                "PartnerTag": self.partner_tag,
                "Resources": [
                    "Images.Primary.Large",
                    "ItemInfo.Title",
                    "ItemInfo.ByLineInfo",
                    "Offers.Listings.Price",
                    "CustomerReviews.Count",
                    "CustomerReviews.StarRating",
                ],
                "SearchIndex": "All",
                "ItemCount": min(limit, 10),
            }
            
            response = requests.post(
                self.endpoint,
                json=payload,
                auth=auth,
                headers={
                    'Content-Type': 'application/x-amz-json-1.1',
                    'X-Amz-Target': 'ProductAdvertisingAPIv1.SearchItems',
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Search failed: {response.status_code} - {response.text[:200]}")
                return []
            
            data = response.json()
            products = []
            
            for item in data.get('SearchResult', {}).get('Items', []):
                product = self._parse_item(item)
                if product:
                    products.append(product)
            
            return products
        
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    def get_items_by_asin(self, asins: List[str]) -> List[Dict]:
        """Fetch products by ASIN"""
        if not asins:
            return []
        
        try:
            auth = AWS4Auth(
                self.access_key,
                self.secret_key,
                self.region,
                self.service
            )
            
            payload = {
                "ItemIds": asins[:10],  # API limit is 10 items
                "PartnerTag": self.partner_tag,
                "Resources": [
                    "Images.Primary.Large",
                    "ItemInfo.Title",
                    "ItemInfo.ByLineInfo",
                    "Offers.Listings.Price",
                    "CustomerReviews.Count",
                    "CustomerReviews.StarRating",
                ],
            }
            
            response = requests.post(
                self.endpoint,
                json=payload,
                auth=auth,
                headers={
                    'Content-Type': 'application/x-amz-json-1.1',
                    'X-Amz-Target': 'ProductAdvertisingAPIv1.GetItems',
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"GetItems failed: {response.status_code}")
                return []
            
            data = response.json()
            products = []
            
            for item in data.get('ItemsResult', {}).get('Items', []):
                product = self._parse_item(item)
                if product:
                    products.append(product)
            
            return products
        
        except Exception as e:
            logger.error(f"Error fetching items by ASIN: {str(e)}")
            return []
    
    def _parse_item(self, item: Dict) -> Optional[Dict]:
        """Parse API response item into product dictionary"""
        try:
            asin = item.get('ASIN')
            if not asin:
                return None
            
            title = item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', '')
            
            price_info = item.get('Offers', {}).get('Listings', [{}])[0].get('Price', {})
            price = price_info.get('DisplayValue', '')
            
            # Extract numeric price
            try:
                price_amount = float(price.replace('$', '').replace(',', ''))
            except (ValueError, AttributeError):
                price_amount = 0.00
            
            image_url = item.get('Images', {}).get('Primary', {}).get('Large', {}).get('URL', '')
            
            affiliate_link = item.get('DetailPageURL', '')
            
            return {
                'asin': asin,
                'title': title,
                'price': price_amount,
                'image_url': image_url,
                'affiliate_link': affiliate_link,
                'raw_data': item,
            }
        
        except Exception as e:
            logger.error(f"Error parsing item: {str(e)}")
            return None
