"""
Serializers for Product and Category models
"""

from rest_framework import serializers
from .models import Product, Category, ProductImage, CategoryImage


class CategoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryImage
        fields = ['id', 'image']


class CategorySerializer(serializers.ModelSerializer):
    images = CategoryImageSerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'amazon_id', 'slug', 'images', 'product_count']

    def get_product_count(self, obj):
        return obj.products.count()


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'asin',
            'title',
            'category',
            'price',
            'description',
            'images',
            'affliliate_link',
            'is_active',
            'created_at',
            'slug',
        ]


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'asin',
            'title',
            'category_name',
            'price',
            'main_image',
            'created_at',
            'slug',
        ]

    def get_main_image(self, obj):
        image = obj.images.first()
        if image:
            return image.image.url
        return None
