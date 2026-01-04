from .client import AmazonPAAPIClient


class AmazonProductService:
    def __init__(self, access_key, secret_key, partner_tag):
        self.client = AmazonPAAPIClient(access_key, secret_key, partner_tag)
        
    def fetch_product(self, asin):
        response = self.client.get_items([asin])

        # If no ItemsResult, bail out
        items = response.get("ItemsResult", {}).get("Items", [])
        
        if not items:
            return None

        item = items[0]

        # Safe lookups with .get()
        title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue")
        image = (
            item.get("Images", {})
                .get("Primary", {})
                .get("Large", {})
                .get("URL")
        )
        price_info = (
            item.get("Offers", {})
                .get("Listings", [{}])[0]
                .get("Price", {})
        )
        price = price_info.get("Amount")
        currency = price_info.get("Currency")
        features = item.get("ItemInfo", {}).get("Features", {}).get("DisplayValues", [])

        return {
            "asin": asin,
            "title": title,
            "image": image,
            "price": price,
            "currency": currency,
            "features": features,
        }
        
    # def fetch_product(self, asin):
    #     response = self.client.get_items([asin])
        
    #     if "ItemsResult" not in response:
    #         return None
        
    #     item = response["ItemsResult"]["Items"][0]
        
    #     return {
    #         "asin": asin,
    #         "title": item["ItemInfo"]["Title"]["DisplayValue"],
    #         "image": item["Images"]["Primary"]["Large"]["URL"],
    #         "price": item["Offers"]["Listings"][0]["Price"]["Amount"],
    #         "currency": item["Offers"]["Listings"][0]["Price"]["Currency"],
    #         "features": item["ItemInfo"].get("Features", {}).get("DisplayValues", []),
    #     }