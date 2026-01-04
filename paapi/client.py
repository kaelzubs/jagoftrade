import json
import hashlib
import hmac
import datetime
import requests


class AmazonPAAPIClient:
    def __init__(self, access_key, secret_key, partner_tag, region="us-east-1"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.region = region
        self.host = "webservices.amazon.com"
        self.endpoint = f"https://{self.host}/paapi5/getitems"
        
    #---------------------------------------------------------------
    # AWS Signature V4 Helpers
    #---------------------------------------------------------------
        
    def sign(self, key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    def _get_signature_key(self, date_stamp):
        k_date = self.sign(("AWS4" + self.secret_key).encode('utf-8'), date_stamp)
        k_region = self.sign(k_date, self.region)
        k_service = self.sign(k_region, "ProductAdvertisingAPI")
        k_signing = self.sign(k_service, "aws4_request")
        return k_signing
    
    #----------------------------------------------------
    # Main Request Method
    #----------------------------------------------------
    def get_items(self, asin_list):
        payload = {
            "ItemIds": asin_list,
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "Offers.Listings.Price",
                "ItemInfo.Features",
                "Details.ProductInfo",  
                "AffiliateInfo.Links",
                "BrowseNodeInfo.BrowseNodes",
            ],
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": "www.amazon.com"
        }
        request_payload = json.dumps(payload)
        
        # Timestamps
        amz_date = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        date_stamp = datetime.datetime.utcnow().strftime('%Y%m%d')
        
        # Canonical request
        canonical_uri = "/paapi5/getitems"
        canonical_headers = (
            f"content-type:application/json\n"
            f"host:{self.host}\n"
            f"x-amz-date:{amz_date}\n"
        )
        signed_headers = "content-type;host;x-amz-date"
        payload_hash = hashlib.sha256(request_payload.encode('utf-8')).hexdigest()
        
        
        canonical_request = (
            f"POST\n{canonical_uri}\n{canonical_uri}\n\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )
        
        # String to sign
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = {
            f"{date_stamp}/{self.region}/ProductAdvertisingAPI/aws4_request"
        }
        string_to_sign = (
            f"{algorithm}\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        
        # Signature
        signing_key = self._get_signature_key(date_stamp)
        signature = hmac.new(
            signing_key, string_to_sign.encode('utf-8'), hashlib.sha256
        ).hexdigest()
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "X-Amz-Date": amz_date,
            "Authorization": (
                f"{algorithm} Credential={self.access_key}/{credential_scope}, "
                f"SignedHeaders={signed_headers}, Signature={signature}"
            ),
        }
        
        # Send request
        response = requests.post(self.endpoint, data=request_payload, headers=headers)
        
        # Production-grade error handling
        try:
            return response.json()
        except Exception:
            return {"Error": "Invalid JSON response", "Raw": response.text}