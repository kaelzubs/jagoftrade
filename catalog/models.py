from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    amazon_id = models.CharField(max_length=20, unique=True)
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
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    title = models.CharField(max_length=200)
    asin = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    affiliate_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at", "title"]
        
    def get_absolute_url(self):
        return reverse("catalog:detail", args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self): return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/")

    def __str__(self):
        return f"Image for {self.product.title}"
