def parse_item_summary(item):
    """Extract a safe subset from PAAPI item."""
    asin = item.get("ASIN")
    detail_page = (item.get("DetailPageURL") or "").strip()

    title = None
    images = {}
    price = None
    currency = None

    item_info = item.get("ItemInfo") or {}
    title_obj = item_info.get("Title") or {}
    if "DisplayValue" in title_obj:
        title = title_obj["DisplayValue"]

    images_obj = item.get("Images") or {}
    primary = images_obj.get("Primary") or {}
    medium = primary.get("Medium") or {}
    large = primary.get("Large") or {}

    images = {
        "medium": medium.get("URL"),
        "large": large.get("URL"),
    }

    offers = item.get("Offers") or {}
    listings = offers.get("Listings") or []
    if listings:
        first = listings[0]
        price_obj = first.get("Price") or {}
        price = price_obj.get("Amount")
        currency = price_obj.get("Currency")

    return {
        "asin": asin,
        "title": title,
        "detail_page_url": detail_page,
        "images": images,
        "price": price,
        "currency": currency,
    }


def parse_search_response(payload):
    items = (payload.get("SearchResult") or {}).get("Items") or []
    return [parse_item_summary(i) for i in items]


def parse_get_items_response(payload):
    items = payload.get("ItemsResult", {}).get("Items") or []
    return [parse_item_summary(i) for i in items]