import argparse
from django.shortcuts import render, get_object_or_404
from .models import Product, Category, ProductImage, CategoryImage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import time


@login_required
def category_list(request, category_slug=None):
    parser = argparse.ArgumentParser(description="Fetch products from Amazon PAAPI")
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,  # safer default for production
        help="Seconds to sleep between product operations"
    )
    args = parser.parse_args()
    category = None
    products = Product.objects.prefetch_related('images').all()
    categories = Category.objects.prefetch_related('images').all()
    time.sleep(args.rate_limit)  # slight delay to reduce load
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category, is_active=True).order_by('-id')
        
    # products = Product.objects.all().order_by('-id')   # or any ordering you prefer
    paginator = Paginator(products, 20)  # 12 products per page
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_obj = paginator.page(paginator.num_pages)
        
    return render(request, 'catalog/category_list.html', {
        'products': products,
        'categories': categories,
        'category': category,
        'page_obj': page_obj
    })

@login_required
def product_list(request, category_slug=None):
    parser = argparse.ArgumentParser(description="Fetch products from Amazon PAAPI")
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,  # safer default for production
        help="Seconds to sleep between product operations"
    )
    args = parser.parse_args()

    category = None
    products = Product.objects.prefetch_related('images').all()
    categories = Category.objects.prefetch_related('images').all()
    time.sleep(args.rate_limit)  # slight delay to reduce load

    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category, is_active=True).order_by('-id')
    
    # products = Product.objects.all().order_by('-id')   # or any ordering you prefer
    paginator = Paginator(products, 20)  # 12 products per page
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'catalog/list.html', {'products': products, 'categories': categories, 'page_obj': page_obj, 'category': category})

@login_required
def product_detail(request, slug):
    parser = argparse.ArgumentParser(description="Fetch products from Amazon PAAPI")
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,  # safer default for production
        help="Seconds to sleep between product operations"
    )
    args = parser.parse_args()
    product = get_object_or_404(Product.objects.prefetch_related('images'), slug=slug, is_active=True)
    time.sleep(args.rate_limit)  # slight delay to reduce load
    return render(request, 'catalog/detail.html', {'product': product})

@login_required
def search_product(request):
    parser = argparse.ArgumentParser(description="Fetch products from Amazon PAAPI")
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,  # safer default for production
        help="Seconds to sleep between product operations"
    )
    args = parser.parse_args()
    query = request.GET.get("q", "")
    products = Product.objects.prefetch_related('images').all()
    time.sleep(args.rate_limit)  # slight delay to reduce load

    if query:
        products = products.filter(Q(title__icontains=query) |
                                   Q(description__icontains=query)).distinct()

    paginator = Paginator(products, 20)  # 12 results per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
        
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'catalog/search.html', {'products': products, 'query': query, 'page_obj': page_obj})