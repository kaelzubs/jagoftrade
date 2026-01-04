from django.core.cache import cache
from .client import PaapiClient
from .schemas import parse_search_response, parse_get_items_response

CACHE_TTL = 300  # seconds

class PaapiService:
    def __init__(self):
        self.client = PaapiClient()

    def search(self, keywords, item_count=10):
        key = f"paapi:search:{keywords}:{item_count}"
        cached = cache.get(key)
        if cached is not None:
            return cached

        raw = self.client.search_items(keywords=keywords, item_count=item_count)
        items = parse_search_response(raw)
        cache.set(key, items, CACHE_TTL)
        return items

    def get_items(self, asins):
        key = f"paapi:get:{','.join(asins)}"
        cached = cache.get(key)
        if cached is not None:
            return cached

        raw = self.client.get_items(asins=asins)
        items = parse_get_items_response(raw)
        cache.set(key, items, CACHE_TTL)
        return items