from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import json
from accounts.models import User
from products.models import Category, Product
from inventory.models import Inventory, StockAlert, InventoryLog
from orders.models import Order


def require_admin(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin_user():
            messages.error(request, 'Admin access required.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@require_admin
def dashboard_home_view(request):
    """Main admin dashboard — all statistics come from the real database."""
    total_products = Product.objects.filter(is_active=True).count()
    total_categories = Category.objects.count()
    total_orders = Order.objects.count()
    total_customers = User.objects.filter(role=User.ROLE_CUSTOMER).count()

    # Total lifetime revenue of valid orders
    total_revenue = Order.objects.filter(
        status__in=['confirmed', 'processing', 'out_for_delivery', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    inv_agg = Inventory.objects.aggregate(
        total_physical=Sum('physical_stock'),
        total_reserved=Sum('reserved_stock')
    )
    total_physical = inv_agg['total_physical'] or 0
    total_reserved = inv_agg['total_reserved'] or 0
    total_available = total_physical - total_reserved

    low_stock_count = Inventory.objects.filter(stock_status='low_stock').count()
    out_of_stock_count = Inventory.objects.filter(stock_status='out_of_stock').count()
    unacknowledged_alerts = StockAlert.objects.filter(is_acknowledged=False).count()

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]
    recent_logs = InventoryLog.objects.select_related(
        'product', 'performed_by'
    ).order_by('-timestamp')[:8]

    # Inventory Overview items
    inventory_items = Inventory.objects.select_related('product', 'product__category').order_by('stock_status', 'product__name')[:8]

    # Active alerts list
    active_alerts = StockAlert.objects.filter(is_acknowledged=False).select_related('product', 'product__category').order_by('-created_at')[:5]

    # 7-day daily trend for Sales Overview Chart
    daily_labels = []
    daily_revenue = []
    daily_orders = []
    today = timezone.now().date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
        day_end = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.max.time()))
        
        day_qs = Order.objects.filter(created_at__range=(day_start, day_end))
        rev = day_qs.filter(status__in=['confirmed', 'processing', 'out_for_delivery', 'delivered']).aggregate(t=Sum('total_amount'))['t'] or 0
        
        daily_labels.append(day.strftime('%b %d'))
        daily_revenue.append(float(rev))
        daily_orders.append(day_qs.count())

    order_status_data = list(Order.objects.values('status').annotate(count=Count('id')))

    week_ago = timezone.now() - timedelta(days=7)
    weekly_revenue = Order.objects.filter(
        created_at__gte=week_ago,
        status__in=['confirmed', 'processing', 'out_for_delivery', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Inventory status breakdown for chart
    inventory_status = list(
        Inventory.objects.values('stock_status').annotate(count=Count('id'))
    )

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'total_physical_stock': total_physical,
        'total_reserved_stock': total_reserved,
        'total_available_stock': total_available,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'unacknowledged_alerts': unacknowledged_alerts,
        'recent_orders': recent_orders,
        'recent_logs': recent_logs,
        'inventory_items': inventory_items,
        'active_alerts': active_alerts,
        'order_status_data': json.dumps(order_status_data),
        'inventory_status': json.dumps(inventory_status),
        'daily_labels': json.dumps(daily_labels),
        'daily_revenue': json.dumps(daily_revenue),
        'daily_orders': json.dumps(daily_orders),
        'weekly_revenue': weekly_revenue,
        'title': 'Admin Dashboard',
    }
    return render(request, 'dashboard/home.html', context)


@require_admin
def product_management_view(request):
    products_qs = Product.objects.select_related('category', 'inventory').all()
    categories = Category.objects.all().order_by('name')

    total_count = products_qs.count()
    active_count = products_qs.filter(is_active=True).count()
    inactive_count = products_qs.filter(is_active=False).count()
    low_stock_count = products_qs.filter(inventory__stock_status__in=['low_stock', 'out_of_stock']).count()

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        products_qs = products_qs.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) | Q(category__name__icontains=q)
        )

    # Category filter
    category_id = request.GET.get('category', '').strip()
    if category_id:
        products_qs = products_qs.filter(category__id=category_id)

    # Status filter
    status = request.GET.get('status', '').strip()
    if status == 'active':
        products_qs = products_qs.filter(is_active=True)
    elif status == 'inactive':
        products_qs = products_qs.filter(is_active=False)
    elif status == 'low_stock':
        products_qs = products_qs.filter(inventory__stock_status__in=['low_stock', 'out_of_stock'])

    # Sorting
    sort = request.GET.get('sort', 'name').strip()
    if sort == 'price_low':
        products_qs = products_qs.order_by('price')
    elif sort == 'price_high':
        products_qs = products_qs.order_by('-price')
    elif sort == 'stock_low':
        products_qs = products_qs.order_by('inventory__physical_stock')
    elif sort == 'stock_high':
        products_qs = products_qs.order_by('-inventory__physical_stock')
    else:
        products_qs = products_qs.order_by('name')

    return render(request, 'dashboard/product_management.html', {
        'products': products_qs,
        'categories': categories,
        'title': 'Product Management',
        'current_q': q,
        'current_category': category_id,
        'current_status': status,
        'current_sort': sort,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'low_stock_count': low_stock_count,
    })


@require_admin
def add_product_view(request):
    from dashboard.forms import ProductForm
    from inventory.services import get_or_create_inventory, restock_product
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            initial_stock = form.cleaned_data.get('initial_stock') or 0
            if initial_stock > 0:
                restock_product(product, initial_stock, request.user, "Initial stock on product creation")
            else:
                get_or_create_inventory(product)
            messages.success(request, f'Product "{product.name}" added successfully.')
            return redirect('dashboard:product_management')
    else:
        form = ProductForm()
    return render(request, 'dashboard/product_form.html', {
        'form': form, 'title': 'Add Product', 'action': 'Add'
    })


@require_admin
def edit_product_view(request, pk):
    from dashboard.forms import ProductForm
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully.')
            return redirect('dashboard:product_management')
    else:
        form = ProductForm(instance=product)
    return render(request, 'dashboard/product_form.html', {
        'form': form, 'product': product, 'title': 'Edit Product', 'action': 'Update'
    })


@require_admin
def toggle_product_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.is_active = not product.is_active
        product.save()
        status_word = 'activated' if product.is_active else 'deactivated'
        messages.success(request, f'Product "{product.name}" has been {status_word}.')
    return redirect('dashboard:product_management')


@require_admin
def category_management_view(request):
    from dashboard.forms import CategoryForm
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('sort_order', 'name')
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('dashboard:category_management')
    else:
        form = CategoryForm()
    return render(request, 'dashboard/category_management.html', {
        'categories': categories,
        'form': form,
        'title': 'Category Management',
    })


@require_admin
def edit_category_view(request, pk):
    from dashboard.forms import CategoryForm
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated.')
            return redirect('dashboard:category_management')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'dashboard/category_form.html', {
        'form': form, 'category': category, 'title': 'Edit Category'
    })
