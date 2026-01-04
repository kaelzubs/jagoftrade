import datetime
import hashlib
import hmac
import json
import requests
from django.conf import settings
from .exceptions import (
    PaapiAuthError, PaapiRateLimitError, PaapiRequestError, PaapiResponseError
)

PAAPI_ENDPOINT = "/paapi5/searchitems"
PAAPI_GETITEMS_ENDPOINT = "/paapi5/getitems"


class PaapiClient:
    def __init__(self):
        cfg = settings.AMAZON_PAAPI
        required = ["ACCESS_KEY", "SECRET_KEY", "PARTNER_TAG", "REGION", "HOST", "MARKETPLACE"]
        missing = [k for k in required if not cfg.get(k)]
        if missing:
            raise PaapiAuthError(f"Missing PAAPI config keys: {', '.join(missing)}")

        self.access_key = cfg["ACCESS_KEY"]
        self.secret_key = cfg["SECRET_KEY"]
        self.partner_tag = cfg["PARTNER_TAG"]
        self.region = cfg["REGION"]
        self.host = cfg["HOST"]
        self.marketplace = cfg["MARKETPLACE"]
        self.timeout = cfg.get("TIMEOUT", 8)
        self.service = "ProductAdvertisingAPI"
        self.base_url = f"https://{self.host}"

    # --- SigV4 helpers ---
    def _sign(self, amz_date, date_stamp, canonical_uri, payload):
        canonical_querystring = ""
        method = "POST"
        canonical_headers = (
            f"content-encoding:{''}\n"
            f"content-type:application/json; charset=UTF-8\n"
            f"host:{self.host}\n"
            f"x-amz-date:{amz_date}\n"
        )
        signed_headers = "content-encoding;content-type;host;x-amz-date"
        payload_hash = hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode("utf-8")).hexdigest()
        canonical_request = "\n".join([
            method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = "\n".join([
            algorithm,
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])

        def _sign_key(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        k_date = _sign_key(("AWS4" + self.secret_key).encode("utf-8"), date_stamp)
        k_region = _sign_key(k_date, self.region)
        k_service = _sign_key(k_region, self.service)
        k_signing = _sign_key(k_service, "aws4_request")
        signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = (
            f"{algorithm} Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return authorization_header, payload_hash

    def _headers(self, amz_date, authorization, payload_hash):
        return {
            "content-encoding": "",
            "content-type": "application/json; charset=UTF-8",
            "host": self.host,
            "x-amz-date": amz_date,
            "x-amz-target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
            "Authorization": authorization,
        }

    def _post(self, uri, payload, target_override=None):
        now = datetime.datetime.utcnow()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        authorization, payload_hash = self._sign(amz_date, date_stamp, uri, payload)

        headers = self._headers(amz_date, authorization, payload_hash)
        if target_override:
            headers["x-amz-target"] = target_override

        try:
            resp = requests.post(
                f"{self.base_url}{uri}",
                headers=headers,
                data=json.dumps(payload, separators=(',', ':')),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise PaapiRequestError(str(e)) from e

        if resp.status_code == 429:
            raise PaapiRateLimitError("PAAPI rate limit exceeded")
        if not (200 <= resp.status_code < 300):
            raise PaapiResponseError(f"PAAPI error: {resp.status_code} {resp.text}")

        try:
            return resp.json()
        except ValueError as e:
            raise PaapiResponseError("Invalid JSON from PAAPI") from e

    # --- Public methods ---
    def search_items(self, keywords, item_count=10, resources=None):
        if not keywords or not isinstance(keywords, str):
            raise PaapiRequestError("keywords must be a non-empty string")

        payload = {
            "Keywords": keywords,
            "ItemCount": int(item_count),
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.marketplace,
            "Resources": resources or [
                "ItemInfo.Title",
                "Images.Primary.Medium",
                "Images.Primary.Large",
                "Offers.Listings.Price",
                "ItemInfo.ByLineInfo",
                "DetailPageURL",
            ],
        }
        return self._post(PAAPI_ENDPOINT, payload)

    def get_items(self, asins, resources=None):
        if not asins or not isinstance(asins, (list, tuple)):
            raise PaapiRequestError("asins must be a list of ASIN strings")

        payload = {
            "ItemIds": list(asins),
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.marketplace,
            "Resources": resources or [
                "ItemInfo.Title",
                "Images.Primary.Large",
                "Offers.Listings.Price",
                "DetailPageURL",
            ],
        }
        target_override = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems"
        return self._post(PAAPI_GETITEMS_ENDPOINT, payload, target_override=target_override)