"""
Simplified PAAPI Service - Pure Python implementation with AWS Signature v4
Does not require requests-aws4auth library
"""

import os
import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

class SimplePAAPIService:
    """Simplified PAAPI v5 service without external signing library"""
    
    def __init__(self):
        self.access_key = os.getenv('AMAZON_ACCESS_KEY')
        self.secret_key = os.getenv('AMAZON_SECRET_KEY')
        self.partner_tag = os.getenv('AMAZON_PARTNER_TAG')
        self.country = os.getenv('AMAZON_COUNTRY', 'US')
        
        if not all([self.access_key, self.secret_key, self.partner_tag]):
            raise ValueError(
                "Missing Amazon PAAPI credentials. "
                "Set AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG"
            )
        
        self.host = 'webservices.amazon.com'
        self.region = self._get_region()
        self.service = 'ProductAdvertisingAPI'
        self.endpoint = f'https://{self.host}/paapi5/getitems'
    
    def _get_region(self) -> str:
        """Map country to AWS region"""
        mapping = {
            'US': 'us-east-1', 'CA': 'us-east-1', 'MX': 'us-east-1',
            'BR': 'us-east-1', 'GB': 'eu-west-1', 'FR': 'eu-west-1',
            'DE': 'eu-west-1', 'IT': 'eu-west-1', 'ES': 'eu-west-1',
            'JP': 'ap-northeast-1', 'IN': 'ap-south-1', 'AU': 'ap-southeast-2',
        }
        return mapping.get(self.country, 'us-east-1')
    
    def search_products(self, keywords: str, limit: int = 10) -> List[Dict]:
        """Search for products by keywords"""
        try:
            payload = {
                "Keywords": keywords,
                "PartnerTag": self.partner_tag,
                "Resources": [
                    "Images.Primary.Large",
                    "ItemInfo.Title",
                    "ItemInfo.ByLineInfo",
                    "Offers.Listings.Price",
                ],
                "SearchIndex": "All",
                "ItemCount": min(limit, 10),
            }
            
            response = self._make_request("SearchItems", payload)
            if not response:
                return []
            
            products = []
            for item in response.get('SearchResult', {}).get('Items', []):
                product = self._parse_item(item)
                if product:
                    products.append(product)
            
            return products
        
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def get_items_by_asin(self, asins: List[str]) -> List[Dict]:
        """Fetch products by ASIN"""
        if not asins:
            return []
        
        try:
            payload = {
                "ItemIds": asins[:10],
                "PartnerTag": self.partner_tag,
                "Resources": [
                    "Images.Primary.Large",
                    "ItemInfo.Title",
                    "Offers.Listings.Price",
                ],
            }
            
            response = self._make_request("GetItems", payload)
            if not response:
                return []
            
            products = []
            for item in response.get('ItemsResult', {}).get('Items', []):
                product = self._parse_item(item)
                if product:
                    products.append(product)
            
            return products
        
        except Exception as e:
            logger.error(f"GetItems error: {str(e)}")
            return []
    
    def _make_request(self, operation: str, payload: Dict) -> Optional[Dict]:
        """Make signed request to PAAPI"""
        try:
            json_body = json.dumps(payload).encode('utf-8')
            
            headers = {
                'Content-Type': 'application/x-amz-json-1.1',
                'X-Amz-Target': f'ProductAdvertisingAPIv1.{operation}',
                'User-Agent': 'jagoftrade/1.0',
            }
            
            # Create signed request
            signed_headers = self._sign_request(
                'POST', self.host, '/paapi5/getitems', headers, json_body
            )
            
            # Make request
            req = urllib.request.Request(
                self.endpoint,
                data=json_body,
                headers=signed_headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            logger.warning(f"HTTP Error {e.code}: {error_body[:200]}")
            return None
        
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    def _sign_request(self, method: str, host: str, path: str, 
                     headers: Dict, body: bytes) -> Dict:
        """Generate AWS Signature Version 4"""
        now = datetime.utcnow()
        amz_date = now.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = now.strftime('%Y%m%d')
        
        # Create canonical request
        headers['Host'] = host
        headers['X-Amz-Date'] = amz_date
        
        signed_headers = ';'.join(sorted(k.lower() for k in headers.keys()))
        
        canonical_headers = '\n'.join(
            f'{k.lower()}:{headers[k]}' for k in sorted(headers.keys())
        ) + '\n'
        
        payload_hash = hashlib.sha256(body).hexdigest()
        
        canonical_request = (
            f'{method}\n{path}\n\n'
            f'{canonical_headers}\n{signed_headers}\n{payload_hash}'
        )
        
        # String to sign
        credential_scope = f'{date_stamp}/{self.region}/{self.service}/aws4_request'
        
        string_to_sign = (
            f'AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n'
            f'{hashlib.sha256(canonical_request.encode()).hexdigest()}'
        )
        
        # Signature
        def sign(key, msg):
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()
        
        k_date = sign(f'AWS4{self.secret_key}'.encode(), date_stamp)
        k_region = sign(k_date, self.region)
        k_service = sign(k_region, self.service)
        k_signing = sign(k_service, 'aws4_request')
        
        signature = hmac.new(k_signing, string_to_sign.encode(), 
                           hashlib.sha256).hexdigest()
        
        # Authorization header
        auth_header = (
            f'AWS4-HMAC-SHA256 Credential={self.access_key}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, Signature={signature}'
        )
        
        headers['Authorization'] = auth_header
        return headers
    
    def _parse_item(self, item: Dict) -> Optional[Dict]:
        """Parse API response item"""
        try:
            asin = item.get('ASIN')
            if not asin:
                return None
            
            title = item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', '')
            
            price_str = item.get('Offers', {}).get('Listings', [{}])[0]\
                .get('Price', {}).get('DisplayValue', '0')
            
            try:
                price = float(price_str.replace('$', '').replace(',', ''))
            except (ValueError, AttributeError):
                price = 0.0
            
            image_url = item.get('Images', {}).get('Primary', {})\
                .get('Large', {}).get('URL', '')
            
            affiliate_link = item.get('DetailPageURL', '')
            
            return {
                'asin': asin,
                'title': title,
                'price': price,
                'image_url': image_url,
                'affiliate_link': affiliate_link,
            }
        
        except Exception as e:
            logger.error(f"Parse error: {str(e)}")
            return None
