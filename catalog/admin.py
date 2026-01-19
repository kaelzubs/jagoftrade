from django.contrib import admin
from .models import Product, Category, ProductImage, CategoryImage


class CategoryImageInline(admin.TabularInline):  # or admin.StackedInline
    model = CategoryImage
    extra = 1   # how many empty forms to display by default


class ProductImageInline(admin.TabularInline):  # or admin.StackedInline
    model = ProductImage
    extra = 1   # how many empty forms to display by default


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'affiliate_link', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('title', 'slug')
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ('Product Info', {
            'fields': ('title', 'category', 'slug', 'price')
        }),
        ('Description & Links', {
            'fields': ('description', 'affiliate_link')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    inlines = [ProductImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')   # ✅ show name & slug in admin list
    search_fields = ('name', 'slug')  # ✅ allow searching categories
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CategoryImageInline]