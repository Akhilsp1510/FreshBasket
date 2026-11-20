from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.db.models import Q, Sum, F
from datetime import datetime
from .models import Inventory, InventoryLog, StockAlert, StockReservation
from .services import restock_product, release_reservation, expire_reservations
from products.models import Product, Category


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
def inventory_list_view(request):
    """
    Primary Inventory Dashboard:
    Computes real-time warehouse aggregates and provides filtering,
    sorting, and health status indicators.
    """
    # Real database calculations (never hardcoded)
    total_products = Product.objects.count()
    physical_agg = Inventory.objects.aggregate(total=Sum('physical_stock'))['total'] or 0
    reserved_agg = Inventory.objects.aggregate(total=Sum('reserved_stock'))['total'] or 0
    available_agg = max(0, physical_agg - reserved_agg)
    in_stock_count = Inventory.objects.filter(stock_status=Inventory.STATUS_IN_STOCK).count()
    low_stock_count = Inventory.objects.filter(stock_status=Inventory.STATUS_LOW_STOCK).count()
    out_of_stock_count = Inventory.objects.filter(stock_status=Inventory.STATUS_OUT_OF_STOCK).count()
    active_reservations_count = StockReservation.objects.filter(
        status=StockReservation.STATUS_ACTIVE,
        expires_at__gt=timezone.now()
    ).count()

    # Queryset for inventory table
    inventories = Inventory.objects.select_related(
        'product', 'product__category'
    ).all()

    # Search filter (product name, brand, category)
    q = request.GET.get('q', '').strip()
    if q:
        inventories = inventories.filter(
            Q(product__name__icontains=q) |
            Q(product__brand__icontains=q) |
            Q(product__category__name__icontains=q)
        )

    # Category filter
    category_id = request.GET.get('category', '').strip()
    if category_id:
        inventories = inventories.filter(product__category__id=category_id)

    # Stock status filter
    status = request.GET.get('status', '').strip()
    if status == 'in_stock':
        inventories = inventories.filter(stock_status=Inventory.STATUS_IN_STOCK)
    elif status == 'low_stock':
        inventories = inventories.filter(stock_status=Inventory.STATUS_LOW_STOCK)
    elif status == 'out_of_stock':
        inventories = inventories.filter(stock_status=Inventory.STATUS_OUT_OF_STOCK)
    elif status == 'has_reservations':
        inventories = inventories.filter(reserved_stock__gt=0)

    # Sorting
    sort = request.GET.get('sort', 'name').strip()
    if sort == 'physical_desc':
        inventories = inventories.order_by('-physical_stock')
    elif sort == 'physical_asc':
        inventories = inventories.order_by('physical_stock')
    elif sort == 'reserved_desc':
        inventories = inventories.order_by('-reserved_stock')
    elif sort == 'stock_low':
        inventories = inventories.order_by('physical_stock', 'stock_status')
    elif sort == 'updated':
        inventories = inventories.order_by('-updated_at')
    else:
        inventories = inventories.order_by('product__name')

    categories = Category.objects.all().order_by('name')

    context = {
        'inventories': inventories,
        'categories': categories,
        'total_products': total_products,
        'total_physical_stock': physical_agg,
        'total_reserved_stock': reserved_agg,
        'total_available_stock': available_agg,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'active_reservations_count': active_reservations_count,
        'current_q': q,
        'current_category': category_id,
        'current_status': status,
        'current_sort': sort,
        'title': 'Inventory Management & Stock Control',
    }
    return render(request, 'inventory/inventory_list.html', context)


@require_admin
def restock_view(request, product_id=None):
    """
    Transaction-safe manual restocking view.
    Can be loaded directly for a specific product or as a general restocking screen.
    """
    product = None
    all_products = []

    if product_id:
        product = get_object_or_404(Product.objects.select_related('inventory', 'category'), pk=product_id)
    else:
        all_products = Product.objects.filter(is_active=True).select_related('inventory', 'category').order_by('name')

    if request.method == 'POST':
        target_product_id = product_id or request.POST.get('product_id')
        if not target_product_id:
            messages.error(request, 'Please select a product to restock.')
            return redirect('inventory:restock_general')

        target_product = get_object_or_404(Product, pk=target_product_id)

        try:
            quantity = int(request.POST.get('quantity', 0))
        except (ValueError, TypeError):
            quantity = 0

        reason = request.POST.get('reason', 'Admin restock').strip() or 'Admin restock'

        if quantity <= 0:
            messages.error(request, 'Restock quantity must be a positive number greater than 0.')
            if product_id:
                return redirect('inventory:restock', product_id=product_id)
            return redirect('inventory:restock_general')

        # Execute transaction-safe restock
        inventory = restock_product(target_product, quantity, request.user, reason)
        messages.success(
            request,
            f'Successfully restocked {quantity} {target_product.get_unit_display()} of "{target_product.name}". '
            f'New physical stock: {inventory.physical_stock}, available: {inventory.available_stock}.'
        )
        return redirect('inventory:inventory_list')

    return render(request, 'inventory/restock.html', {
        'product': product,
        'inventory': getattr(product, 'inventory', None) if product else None,
        'all_products': all_products,
        'title': f'Restock: {product.name}' if product else 'Manual Warehouse Restock',
    })


@require_admin
def reservations_view(request):
    """
    Dedicated Stock Reservation Monitoring:
    Tracks active checkout holds, confirmed sales, expired carts, and releases.
    """
    now = timezone.now()
    reservations_qs = StockReservation.objects.select_related(
        'user', 'product', 'product__category'
    ).all()

    # Aggregate counts across all states
    total_count = reservations_qs.count()
    active_count = StockReservation.objects.filter(status=StockReservation.STATUS_ACTIVE, expires_at__gt=now).count()
    confirmed_count = StockReservation.objects.filter(status=StockReservation.STATUS_CONFIRMED).count()
    expired_count = StockReservation.objects.filter(
        Q(status=StockReservation.STATUS_EXPIRED) |
        Q(status=StockReservation.STATUS_ACTIVE, expires_at__lte=now)
    ).count()
    cancelled_count = StockReservation.objects.filter(status=StockReservation.STATUS_CANCELLED).count()

    # Search filter (username, email, product name)
    q = request.GET.get('q', '').strip()
    if q:
        reservations_qs = reservations_qs.filter(
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(product__name__icontains=q)
        )

    # Status filter
    status = request.GET.get('status', 'active').strip()
    if status == 'active':
        reservations_qs = reservations_qs.filter(status=StockReservation.STATUS_ACTIVE, expires_at__gt=now)
    elif status == 'confirmed':
        reservations_qs = reservations_qs.filter(status=StockReservation.STATUS_CONFIRMED)
    elif status == 'expired':
        reservations_qs = reservations_qs.filter(
            Q(status=StockReservation.STATUS_EXPIRED) |
            Q(status=StockReservation.STATUS_ACTIVE, expires_at__lte=now)
        )
    elif status == 'cancelled':
        reservations_qs = reservations_qs.filter(status=StockReservation.STATUS_CANCELLED)
    # If status == 'all', no filter applied

    reservations_qs = reservations_qs.order_by('-created_at')[:200]

    context = {
        'reservations': reservations_qs,
        'current_status': status,
        'current_q': q,
        'total_count': total_count,
        'active_count': active_count,
        'confirmed_count': confirmed_count,
        'expired_count': expired_count,
        'cancelled_count': cancelled_count,
        'now': now,
        'title': 'Active Stock Reservations & Cart Holds',
    }
    return render(request, 'inventory/reservations.html', context)


@require_admin
def cancel_reservation_view(request, pk):
    """Manually cancel an active reservation from admin dashboard."""
    reservation = get_object_or_404(StockReservation, pk=pk)
    if request.method == 'POST':
        if reservation.status == StockReservation.STATUS_ACTIVE:
            release_reservation(
                reservation,
                performed_by=request.user,
                reason="Admin manual release from Reservations dashboard"
            )
            messages.success(request, f'Reservation #{reservation.id} for "{reservation.product.name}" released.')
        else:
            messages.warning(request, f'Reservation #{reservation.id} is already {reservation.status}.')
    return redirect('inventory:reservations')


@require_admin
def inventory_log_view(request):
    """
    Tamper-Evident Inventory Activity & Audit Ledger:
    Append-only chronological record of every physical and reserved stock delta.
    Includes aggregate movement counts, search, product filter, type filter,
    date range filtering, and pagination.
    """
    # Summary calculation cards
    total_transactions = InventoryLog.objects.count()
    restock_transactions = InventoryLog.objects.filter(change_type=InventoryLog.CHANGE_RESTOCK).count()
    reservation_transactions = InventoryLog.objects.filter(
        change_type__in=[InventoryLog.CHANGE_RESERVATION, InventoryLog.CHANGE_RESERVATION_RELEASE]
    ).count()
    sales_transactions = InventoryLog.objects.filter(change_type=InventoryLog.CHANGE_SALE).count()
    cancellation_transactions = InventoryLog.objects.filter(change_type=InventoryLog.CHANGE_CANCELLATION).count()

    logs_qs = InventoryLog.objects.select_related(
        'product', 'product__category', 'performed_by', 'reference_order', 'reference_reservation'
    ).all()

    # Search filter (product name, actor username, order number, reason)
    q = request.GET.get('q', '').strip()
    if q:
        logs_qs = logs_qs.filter(
            Q(product__name__icontains=q) |
            Q(performed_by__username__icontains=q) |
            Q(reason__icontains=q) |
            Q(reference_order__order_number__icontains=q)
        )

    # Product filter
    product_id = request.GET.get('product', '').strip()
    if product_id:
        logs_qs = logs_qs.filter(product__id=product_id)

    # Movement type filter
    change_type = request.GET.get('type', '').strip()
    if change_type and change_type != 'all':
        logs_qs = logs_qs.filter(change_type=change_type)

    # Date range filters
    date_from = request.GET.get('date_from', '').strip()
    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            logs_qs = logs_qs.filter(timestamp__date__gte=d_from)
        except ValueError:
            pass

    date_to = request.GET.get('date_to', '').strip()
    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            logs_qs = logs_qs.filter(timestamp__date__lte=d_to)
        except ValueError:
            pass

    logs_qs = logs_qs.order_by('-timestamp')

    # Pagination: 30 logs per page
    paginator = Paginator(logs_qs, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    all_products = Product.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'all_products': all_products,
        'total_transactions': total_transactions,
        'restock_transactions': restock_transactions,
        'reservation_transactions': reservation_transactions,
        'sales_transactions': sales_transactions,
        'cancellation_transactions': cancellation_transactions,
        'current_type': change_type,
        'current_product': product_id,
        'current_q': q,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'change_type_choices': InventoryLog.CHANGE_TYPE_CHOICES,
        'title': 'Inventory Activity & Audit Ledger',
    }
    return render(request, 'inventory/inventory_log.html', context)


@require_admin
def alerts_view(request):
    """
    Stock Alerts Dashboard:
    Computes real-time alert statistics and renders alert management table
    with filtering by status, alert type, keyword search, and pagination.
    """
    total_alerts = StockAlert.objects.count()
    unacknowledged_alerts_count = StockAlert.objects.filter(is_acknowledged=False).count()
    low_stock_alerts_count = StockAlert.objects.filter(alert_type=StockAlert.ALERT_LOW_STOCK).count()
    out_of_stock_alerts_count = StockAlert.objects.filter(alert_type=StockAlert.ALERT_OUT_OF_STOCK).count()
    acknowledged_alerts_count = StockAlert.objects.filter(is_acknowledged=True).count()

    alerts_qs = StockAlert.objects.select_related(
        'product', 'product__category', 'product__inventory', 'acknowledged_by'
    ).all()

    # Search filter (product name)
    q = request.GET.get('q', '').strip()
    if q:
        alerts_qs = alerts_qs.filter(product__name__icontains=q)

    # Status / Type Filter
    status = request.GET.get('status', 'unacknowledged').strip()
    if status == 'unacknowledged':
        alerts_qs = alerts_qs.filter(is_acknowledged=False)
    elif status == 'acknowledged':
        alerts_qs = alerts_qs.filter(is_acknowledged=True)
    elif status == 'low_stock':
        alerts_qs = alerts_qs.filter(alert_type=StockAlert.ALERT_LOW_STOCK)
    elif status == 'out_of_stock':
        alerts_qs = alerts_qs.filter(alert_type=StockAlert.ALERT_OUT_OF_STOCK)
    # If status == 'all', show all records

    alerts_qs = alerts_qs.order_by('-created_at')

    # Pagination: 25 alerts per page
    paginator = Paginator(alerts_qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'alerts': page_obj.object_list,
        'total_alerts': total_alerts,
        'unacknowledged_alerts': unacknowledged_alerts_count,
        'low_stock_alerts_count': low_stock_alerts_count,
        'out_of_stock_alerts_count': out_of_stock_alerts_count,
        'acknowledged_alerts_count': acknowledged_alerts_count,
        'current_status': status,
        'current_q': q,
        'title': 'Stock Alerts',
    }
    return render(request, 'inventory/alerts.html', context)


@require_admin
def acknowledge_alert_view(request, pk):
    alert = get_object_or_404(StockAlert, pk=pk)
    if request.method == 'POST':
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        messages.success(request, f'Stock alert for "{alert.product.name}" successfully acknowledged.')
    return redirect('inventory:alerts')


@require_admin
def expire_reservations_view(request):
    """Manual trigger for expiring stale reservations."""
    if request.method == 'POST':
        count = expire_reservations()
        if count > 0:
            messages.success(request, f'Expired {count} stale reservation(s) and returned units to available stock.')
        else:
            messages.info(request, 'No expired reservations found. All active reservations are within the 10-minute hold window.')
    return redirect('inventory:inventory_list')
