from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    
    class Meta:
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self): return self.name
    
class CategoryImage(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="category_images/")

    def __str__(self):
        return f"Image for {self.category.name}"

class Product(models.Model):
    """
    Represents a product in the catalog.
    Each product belongs to a category and has a unique ASIN identifier.
    """

    category = models.ForeignKey("Category", on_delete=models.PROTECT,related_name="products",  help_text="Category this product belongs to.")
    title = models.CharField(max_length=200, help_text="Title of the product.")
    asin = models.CharField(max_length=20, unique=True, help_text="Amazon Standard Identification Number (ASIN).")
    slug = models.SlugField(max_length=220, unique=True, blank=True, help_text="URL-friendly identifier generated from the title.")
    brand = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, default="USD")
    description = models.TextField(blank=True, help_text="Detailed description of the product.")
    price = models.DecimalField( max_digits=10, decimal_places=2, help_text="Price of the product.")
    affiliate_link = models.URLField(blank=True,  help_text="Affiliate purchase link.")
    is_active = models.BooleanField(default=True, help_text="Whether the product is active and visible.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the product was created.")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "title"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def get_absolute_url(self):
        """Return the canonical URL for this product."""
        return reverse("catalog:detail", args=[self.slug])

    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.asin})"


class ProductImage(models.Model):
    """
    Represents an image associated with a product.
    Multiple images can be linked to a single product.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", help_text="The product this image belongs to.")
    image = models.ImageField(help_text="URL of the product image.",)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image for {self.product.title}"

