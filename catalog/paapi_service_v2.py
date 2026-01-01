import os
import json
import time
import logging
import hashlib
import hmac
import datetime
from typing import Dict, List

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class AmazonPAAPIService:
    """
    Wrapper for Amazon Product Advertising API (PAAPI v5).
    Provides search functionality for products.
    """

    def __init__(self):
        self.access_key = os.getenv("AMAZON_ACCESS_KEY")
        self.secret_key = os.getenv("AMAZON_SECRET_KEY")
        self.partner_tag = os.getenv("AMAZON_PARTNER_TAG")
        self.partner_type = os.getenv("AMAZON_PARTNER_TYPE", "Associates")
        self.region = os.getenv("AMAZON_REGION", "us-east-1")
        self.country = os.getenv("AMAZON_COUNTRY", "US")
        self.host = os.getenv("AMAZON_HOST")
        self.marketplace = os.getenv("AMAZON_MARKETPLACE")

        # Host (API endpoint) vs Marketplace (payload)
        self.marketplace = os.getenv("AMAZON_MARKETPLACE")

        self.timeout = int(os.getenv("AMAZON_TIMEOUT", 10))
        self.max_retries = int(os.getenv("AMAZON_MAX_RETRIES", 3))

        if not all([self.access_key, self.secret_key, self.partner_tag, self.host, self.region, self.marketplace]):
            raise RuntimeError("Amazon PAAPI credentials are missing")

        self.endpoint = f"https://{self.host}/paapi5/searchitems"

    # --- AWS Signature V4 helpers ---
    def _sign(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signature_key(self, key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
        k_date = self._sign(("AWS4" + key).encode("utf-8"), date_stamp)
        k_region = self._sign(k_date, region_name)
        k_service = self._sign(k_region, service_name)
        k_signing = self._sign(k_service, "aws4_request")
        return k_signing

    def _signed_headers(self, payload: str) -> Dict[str, str]:
        method = "POST"
        service = "ProductAdvertisingAPI"
        host = self.marketplace
        content_type = "application/json; charset=UTF-8"

        t = datetime.datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")  # Date w/o time

        canonical_uri = "/paapi5/searchitems"
        canonical_querystring = ""
        canonical_headers = f"content-type:{content_type}\nhost:{host}\nx-amz-date:{amz_date}\n"
        signed_headers = "content-type;host;x-amz-date"
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (
            f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
            f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.region}/{service}/aws4_request"
        string_to_sign = (
            f"{algorithm}\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        signing_key = self._get_signature_key(str(self.secret_key), date_stamp, self.region, service)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = (
            f"{algorithm} Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers = {
            "Content-Type": content_type,
            "X-Amz-Date": amz_date,
            "Authorization": authorization_header,
            "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
            "Host": host,
        }
        return headers

    # --- Public API ---
    def search_products(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search products by keyword using PAAPI v5.
        Returns a list of product dictionaries.
        """
        payload = {
            "Keywords": keyword,
            "ASSOCIATE_TAG": self.partner_tag,
            "AWSAccessKeyId": self.access_key,
            "SecretKey": self.secret_key,
            "PartnerTag": self.partner_tag,
            "PartnerType": self.partner_type,
            "Host": self.host,
            "Region": self.region,
            "Marketplace": self.marketplace, # FIXED: must be www.amazon.com, not webservices.amazon.com
            "Resources": [
                "ItemInfo.Title",
                "ItemInfo.Features",
                "ItemInfo.ByLineInfo",
                "Offers.Listings.Price",
                "Images.Primary.Medium",
            ],
            "SearchIndex": "All",
            "ItemCount": min(limit, 10),  # Amazon max is 10
        }

        json_payload = json.dumps(payload)
        headers = self._signed_headers(json_payload)

        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.post(
                    self.endpoint,
                    data=json_payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()

                items = data.get("SearchResult", {}).get("Items", [])
                results = []
                for item in items:
                    asin = item.get("ASIN")
                    title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue")
                    description = item.get("ItemInfo", {}).get("Features", {}).get("DisplayValues", [""])
                    price = (
                        item.get("Offers", {})
                        .get("Listings", [{}])[0]
                        .get("Price", {})
                        .get("DisplayAmount")
                    )
                    image_url = (
                        item.get("Images", {})
                        .get("Primary", {})
                        .get("Medium", {})
                        .get("URL")
                    )
                    affiliate_link = item.get("DetailPageURL")

                    results.append(
                        {
                            "asin": asin,
                            "title": title,
                            "description": " ".join(description),
                            "price": price,
                            "image_url": image_url,
                            "affiliate_link": affiliate_link,
                        }
                    )
                return results

            except RequestException as exc:
                retries += 1
                logger.warning(
                    "PAAPI request failed (attempt %d/%d): %s",
                    retries,
                    self.max_retries,
                    exc,
                )
                time.sleep(2 ** retries)  # exponential backoff
            except Exception as exc:
                logger.error("Unexpected PAAPI error: %s", exc, exc_info=True)
                break

        return []