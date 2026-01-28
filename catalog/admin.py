from django.contrib import admin
from .models import Product, Category, ProductImage, CategoryImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class CategoryImageInline(admin.TabularInline):
    model = CategoryImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('title', 'slug')
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductImageInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')  # add this for clarity
    search_fields = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CategoryImageInline]