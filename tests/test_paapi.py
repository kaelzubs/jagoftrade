import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.conf import settings

class PaapiIntegrationTests(TestCase):
    def setUp(self):
        # Ensure test config is present (use dummy keys)
        settings.AMAZON_PAAPI["ACCESS_KEY"] = settings.AMAZON_PAAPI.get("ACCESS_KEY") or "TESTACCESS"
        settings.AMAZON_PAAPI["SECRET_KEY"] = settings.AMAZON_PAAPI.get("SECRET_KEY") or "TESTSECRET"
        settings.AMAZON_PAAPI["PARTNER_TAG"] = settings.AMAZON_PAAPI.get("PARTNER_TAG") or "testtag-20"
        settings.AMAZON_PAAPI["REGION"] = settings.AMAZON_PAAPI.get("REGION") or "us-east-1"
        settings.AMAZON_PAAPI["HOST"] = settings.AMAZON_PAAPI.get("HOST") or "webservices.amazon.com"
        settings.AMAZON_PAAPI["MARKETPLACE"] = settings.AMAZON_PAAPI.get("MARKETPLACE") or "www.amazon.com"
        self.client = Client()

    @patch("yourapp.paapi.client.requests.post")
    def test_search_endpoint(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json = lambda: {
            "SearchResult": {
                "Items": [
                    {
                        "ASIN": "B00TEST",
                        "DetailPageURL": "https://www.amazon.com/dp/B00TEST",
                        "ItemInfo": {"Title": {"DisplayValue": "Test Product"}},
                        "Images": {"Primary": {"Medium": {"URL": "m.jpg"}, "Large": {"URL": "l.jpg"}}},
                        "Offers": {"Listings": [{"Price": {"Amount": 19.99, "Currency": "USD"}}]},
                    }
                ]
            }
        }
        resp = self.client.get("/api/paapi/search?q=keyboard&count=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["asin"] == "B00TEST"

    @patch("yourapp.paapi.client.requests.post")
    def test_get_items_endpoint(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json = lambda: {
            "ItemsResult": {
                "Items": [
                    {
                        "ASIN": "B00TEST2",
                        "DetailPageURL": "https://www.amazon.com/dp/B00TEST2",
                        "ItemInfo": {"Title": {"DisplayValue": "Another Product"}},
                        "Images": {"Primary": {"Large": {"URL": "L2.jpg"}}},
                        "Offers": {"Listings": [{"Price": {"Amount": 29.99, "Currency": "USD"}}]},
                    }
                ]
            }
        }
        resp = self.client.get("/api/paapi/items?asins=B00TEST2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["price"] == 29.99