# shop/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from catalog.models import Product, Category

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.created_at  # assuming you track updates

class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return reverse("catalog:detail", args=[obj.slug])

class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return [
            "core:home",
            "suppliers:terms",
            "suppliers:privacy",
            "suppliers:shipping_returns",
            "suppliers:faq",
            "suppliers:about_us",
            "accounts:contact",  
        ]

    def location(self, item):
        return reverse(item)