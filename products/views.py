from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product


def home_view(request):
    """
    Blinkit-style homepage with visual category tiles, promotional quick-commerce banners,
    and curated product aisles for daily essentials.
    """
    categories = Category.objects.filter(is_active=True).order_by('sort_order')
    featured_products = Product.objects.filter(
        is_active=True, is_featured=True
    ).select_related('category', 'inventory')[:8]
    
    # Specific aisles for Blinkit look & feel
    dairy_products = Product.objects.filter(
        category__name__icontains='Dairy', is_active=True
    ).select_related('category', 'inventory')[:6]
    
    veggie_products = Product.objects.filter(
        category__name__icontains='Fruits', is_active=True
    ).select_related('category', 'inventory')[:6]

    snack_products = Product.objects.filter(
        category__name__icontains='Snacks', is_active=True
    ).select_related('category', 'inventory')[:6]

    staple_products = Product.objects.filter(
        category__name__icontains='Grains', is_active=True
    ).select_related('category', 'inventory')[:6]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'dairy_products': dairy_products,
        'veggie_products': veggie_products,
        'snack_products': snack_products,
        'staple_products': staple_products,
        'title': 'FreshBasket - 10-Minute Grocery Delivery',
    }
    return render(request, 'products/home.html', context)


def product_list_view(request):
    """Product listing with search, filter, sort and pagination."""
    products = Product.objects.filter(is_active=True).select_related('category', 'inventory')
    categories = Category.objects.filter(is_active=True)

    # Search
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(brand__icontains=query)
        )

    # Category filter
    category_slug = request.GET.get('category', '')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=selected_category)

    # Sort
    sort = request.GET.get('sort', 'name')
    sort_options = {
        'name': 'name',
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
    }
    products = products.order_by(sort_options.get(sort, 'name'))

    # Pagination
    paginator = Paginator(products, 16)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'query': query,
        'sort': sort,
        'title': 'All Products',
    })


def product_detail_view(request, slug):
    """Product detail page with stock status and add to cart."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    substitutes = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(pk=product.pk).select_related('inventory')[:4]
    context = {
        'product': product,
        'substitutes': substitutes,
        'title': product.name,
    }
    return render(request, 'products/product_detail.html', context)


def category_list_view(request):
    """All categories page."""
    categories = Category.objects.filter(is_active=True).order_by('sort_order')
    return render(request, 'products/category_list.html', {
        'categories': categories,
        'title': 'Shop by Category',
    })
