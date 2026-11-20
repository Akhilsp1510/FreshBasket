from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from datetime import datetime
from decimal import Decimal
from .models import Cart, CartItem, Order, OrderItem, Payment
from .forms import CheckoutForm
from products.models import Product
from inventory.services import (
    reserve_stock, release_reservation, confirm_reservation,
    restore_stock_on_cancellation, InsufficientStockError
)


def require_admin(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin_user():
            messages.error(request, 'Admin access required.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── CART VIEWS ──────────────────────────────────────────────────────────────

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related(
        'product', 'product__inventory', 'specific_substitute'
    ).all()
    subtotal = cart.get_total()
    delivery_fee = Decimal('40.00') if subtotal > 0 else Decimal('0.00')
    total = subtotal + delivery_fee
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'title': 'My Cart',
    })


@login_required
def add_to_cart_view(request, product_id):
    if request.method != 'POST':
        return redirect('products:product_list')

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        quantity = 1
    substitution_pref = request.POST.get('substitution_preference', 'none')

    available = product.get_available_stock()
    if available <= 0:
        messages.error(request, f'Sorry, {product.name} is currently out of stock.')
        return redirect('products:product_detail', slug=product.slug)

    if quantity > available:
        messages.warning(request, f'Only {available} unit(s) of {product.name} available. Adjusted quantity.')
        quantity = available

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity, 'substitution_preference': substitution_pref}
    )

    if not created:
        new_qty = min(cart_item.quantity + quantity, available)
        cart_item.quantity = new_qty
        cart_item.substitution_preference = substitution_pref
        cart_item.save()
        messages.success(request, f'Updated quantity of {product.name} in cart.')
    else:
        messages.success(request, f'{product.name} added to cart!')

    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)


@login_required
def update_cart_view(request, item_id):
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'remove':
            product_name = cart_item.product.name
            cart_item.delete()
            messages.info(request, f'{product_name} removed from cart.')
        elif action == 'update':
            try:
                quantity = int(request.POST.get('quantity', 1))
            except ValueError:
                quantity = 1
            available = cart_item.product.get_available_stock()
            if quantity > available:
                quantity = available
                messages.warning(request, f'Only {available} unit(s) of {cart_item.product.name} available.')
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.substitution_preference = request.POST.get(
                    'substitution_preference', cart_item.substitution_preference
                )
                cart_item.save()
            else:
                product_name = cart_item.product.name
                cart_item.delete()
                messages.info(request, f'{product_name} removed from cart.')
    return redirect('orders:cart')


# ─── CHECKOUT VIEWS ───────────────────────────────────────────────────────────

@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related('product', 'product__inventory').all()

    if not items.exists():
        messages.warning(request, 'Your cart is empty. Add some products first!')
        return redirect('products:product_list')

    saved_addresses = request.user.addresses.all()
    default_address = saved_addresses.filter(is_default=True).first()

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            reservations = []
            failed_items = []

            # Step 1: Reserve stock for each cart item
            for item in items:
                try:
                    reservation = reserve_stock(request.user, item.product, item.quantity)
                    reservations.append((item, reservation))
                except InsufficientStockError as e:
                    failed_items.append(str(e))

            if failed_items:
                # Rollback all reservations made so far
                for _, res in reservations:
                    try:
                        release_reservation(res, request.user, "Checkout failed — partial rollback")
                    except Exception:
                        pass
                for msg in failed_items:
                    messages.error(request, msg)
                subtotal = sum(item.product.price * item.quantity for item in items)
                return render(request, 'orders/checkout.html', {
                    'form': form, 'cart': cart, 'items': items,
                    'saved_addresses': saved_addresses,
                    'subtotal': subtotal, 'delivery_fee': Decimal('40.00'),
                    'total': subtotal + Decimal('40.00'), 'title': 'Checkout',
                })

            # Step 2: Create order
            with transaction.atomic():
                subtotal = sum(item.product.price * item.quantity for item in items)
                delivery_fee = Decimal('40.00')

                order = Order.objects.create(
                    user=request.user,
                    payment_method=form.cleaned_data['payment_method'],
                    delivery_full_name=form.cleaned_data['full_name'],
                    delivery_phone=form.cleaned_data['phone'],
                    delivery_address_line1=form.cleaned_data['address_line1'],
                    delivery_address_line2=form.cleaned_data.get('address_line2', ''),
                    delivery_city=form.cleaned_data['city'],
                    delivery_state=form.cleaned_data['state'],
                    delivery_pincode=form.cleaned_data['pincode'],
                    subtotal=subtotal,
                    delivery_fee=delivery_fee,
                    notes=form.cleaned_data.get('notes', ''),
                )

                # Step 3: Create order items + confirm reservations
                for item, reservation in reservations:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        product_price=item.product.price,
                        quantity=item.quantity,
                        substitution_preference=item.substitution_preference,
                    )
                    confirm_reservation(reservation, order)

                # Step 4: Payment record
                Payment.objects.create(
                    order=order,
                    amount=order.total_amount,
                    method=order.payment_method,
                    status='paid' if order.payment_method == 'simulated' else 'pending',
                )

                # Step 5: Clear cart
                cart.items.all().delete()

            messages.success(request, f'Order #{order.order_number} placed successfully! 🎉')
            return redirect('orders:order_confirmation', order_number=order.order_number)
    else:
        initial = {}
        if default_address:
            initial = {
                'full_name': default_address.full_name,
                'phone': default_address.phone,
                'address_line1': default_address.address_line1,
                'address_line2': default_address.address_line2,
                'city': default_address.city,
                'state': default_address.state,
                'pincode': default_address.pincode,
            }
        form = CheckoutForm(initial=initial)

    subtotal = sum(item.product.price * item.quantity for item in items)
    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'items': items,
        'saved_addresses': saved_addresses,
        'subtotal': subtotal,
        'delivery_fee': Decimal('40.00'),
        'total': subtotal + Decimal('40.00'),
        'title': 'Checkout',
    })


@login_required
def order_confirmation_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_confirmation.html', {
        'order': order,
        'title': f'Order #{order.order_number} Confirmed!',
    })


@login_required
def my_orders_view(request):
    all_user_orders = Order.objects.filter(user=request.user).prefetch_related('items', 'items__product')
    
    total_count = all_user_orders.count()
    ongoing_orders = all_user_orders.filter(status__in=[
        Order.STATUS_PENDING,
        Order.STATUS_CONFIRMED,
        Order.STATUS_PROCESSING,
        Order.STATUS_OUT_FOR_DELIVERY
    ])
    ongoing_count = ongoing_orders.count()
    completed_orders = all_user_orders.filter(status=Order.STATUS_DELIVERED)
    completed_count = completed_orders.count()
    cancelled_orders = all_user_orders.filter(status=Order.STATUS_CANCELLED)
    cancelled_count = cancelled_orders.count()

    # Filter by tab
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'ongoing':
        orders = ongoing_orders
    elif status_filter == 'completed':
        orders = completed_orders
    elif status_filter == 'cancelled':
        orders = cancelled_orders
    else:
        orders = all_user_orders

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        orders = orders.order_by('created_at')
    elif sort_by == 'highest':
        orders = orders.order_by('-total_amount')
    elif sort_by == 'lowest':
        orders = orders.order_by('total_amount')
    else:
        orders = orders.order_by('-created_at')

    return render(request, 'orders/my_orders.html', {
        'orders': orders,
        'title': 'My Orders',
        'current_status': status_filter,
        'current_sort': sort_by,
        'total_count': total_count,
        'ongoing_count': ongoing_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    })


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items', 'items__product'),
        order_number=order_number,
        user=request.user
    )
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'title': f'Order #{order.order_number}',
    })


@login_required
def cancel_order_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method == 'POST':
        if order.can_cancel():
            order.status = Order.STATUS_CANCELLED
            order.save()
            restore_stock_on_cancellation(order, performed_by=request.user)
            messages.success(request, f'Order #{order.order_number} has been cancelled and stock restored.')
        else:
            messages.error(request, 'This order cannot be cancelled at this stage.')
    return redirect('orders:order_detail', order_number=order_number)


# ─── ADMIN ORDER VIEWS ────────────────────────────────────────────────────────

@require_admin
def admin_orders_view(request):
    """
    Enterprise Admin Order Management:
    Real-time database order metrics, advanced filters (search, status, date range),
    sorting, and pagination.
    """
    # Live database metrics (never hardcoded)
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status=Order.STATUS_PENDING).count()
    confirmed_orders = Order.objects.filter(status=Order.STATUS_CONFIRMED).count()
    processing_orders = Order.objects.filter(status=Order.STATUS_PROCESSING).count()
    out_for_delivery_orders = Order.objects.filter(status=Order.STATUS_OUT_FOR_DELIVERY).count()
    delivered_orders = Order.objects.filter(status=Order.STATUS_DELIVERED).count()
    cancelled_orders = Order.objects.filter(status=Order.STATUS_CANCELLED).count()
    total_revenue = Order.objects.exclude(status=Order.STATUS_CANCELLED).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    orders_qs = Order.objects.select_related(
        'user', 'payment'
    ).prefetch_related(
        'items', 'items__product'
    ).all()

    # Search filter (order ID, username, email, recipient, phone)
    q = request.GET.get('q', '').strip()
    if q:
        clean_q = q.lstrip('#')
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=clean_q) |
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(delivery_full_name__icontains=q) |
            Q(delivery_phone__icontains=q)
        )

    # Status filter
    status = request.GET.get('status', '').strip()
    valid_status_keys = [s[0] for s in Order.STATUS_CHOICES]
    if status in valid_status_keys:
        orders_qs = orders_qs.filter(status=status)

    # Date range filters
    date_from = request.GET.get('date_from', '').strip()
    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            orders_qs = orders_qs.filter(created_at__date__gte=d_from)
        except ValueError:
            pass

    date_to = request.GET.get('date_to', '').strip()
    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            orders_qs = orders_qs.filter(created_at__date__lte=d_to)
        except ValueError:
            pass

    # Sorting
    sort = request.GET.get('sort', 'newest').strip()
    if sort == 'oldest':
        orders_qs = orders_qs.order_by('created_at')
    elif sort == 'amount_high':
        orders_qs = orders_qs.order_by('-total_amount')
    elif sort == 'amount_low':
        orders_qs = orders_qs.order_by('total_amount')
    else:
        orders_qs = orders_qs.order_by('-created_at')

    # Pagination: 20 orders per page
    paginator = Paginator(orders_qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'processing_orders': processing_orders,
        'out_for_delivery_orders': out_for_delivery_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'current_status': status,
        'current_q': q,
        'current_sort': sort,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'status_choices': Order.STATUS_CHOICES,
        'title': 'Order Management',
    }
    return render(request, 'orders/admin_orders.html', context)


@require_admin
def admin_order_detail_view(request, order_number):
    """
    Detailed Order Management & Operations:
    Full customer shipping dossier, itemized breakdown, visual status timeline,
    transaction-safe inventory audit trail, and status transition manager.
    """
    from django.utils import timezone
    order = get_object_or_404(
        Order.objects.select_related('user', 'payment').prefetch_related(
            'items', 'items__product', 'inventory_logs', 'inventory_logs__product'
        ),
        order_number=order_number
    )

    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]

        if new_status in valid_statuses and new_status != order.status:
            # Handle cancellation & inventory restoration
            if new_status == Order.STATUS_CANCELLED:
                if order.can_cancel():
                    restore_stock_on_cancellation(order, performed_by=request.user)
                    messages.success(request, f'Order #{order.order_number} cancelled and stock safely restored to inventory.')
                else:
                    messages.error(request, f'Order #{order.order_number} cannot be cancelled as it is already {order.get_status_display()}.')
                    return redirect('orders:admin_order_detail', order_number=order.order_number)

            order.status = new_status

            # If marked delivered, update payment for COD if pending
            if new_status == Order.STATUS_DELIVERED and hasattr(order, 'payment'):
                payment = order.payment
                if payment.status == 'pending':
                    payment.status = 'paid'
                    payment.paid_at = timezone.now()
                    payment.save()

            order.save()
            messages.success(
                request,
                f'Order #{order.order_number} status updated to "{order.get_status_display()}".'
            )
        elif new_status == order.status:
            messages.info(request, f'Order #{order.order_number} is already marked as "{order.get_status_display()}".')
        else:
            messages.error(request, 'Invalid status choice provided.')

        return redirect('orders:admin_order_detail', order_number=order.order_number)

    # Milestones for timeline
    milestones = [
        {'key': Order.STATUS_PENDING, 'label': 'Order Placed', 'icon': 'bi-cart-check', 'description': 'Customer checked out'},
        {'key': Order.STATUS_CONFIRMED, 'label': 'Confirmed', 'icon': 'bi-patch-check', 'description': 'Inventory verified'},
        {'key': Order.STATUS_PROCESSING, 'label': 'Processing (Packing)', 'icon': 'bi-box-seam', 'description': 'Items picked & packaged'},
        {'key': Order.STATUS_OUT_FOR_DELIVERY, 'label': 'Out for Delivery', 'icon': 'bi-truck', 'description': 'Courier dispatched'},
        {'key': Order.STATUS_DELIVERED, 'label': 'Delivered', 'icon': 'bi-house-check', 'description': 'Customer received package'},
    ]

    status_order_map = {
        Order.STATUS_PENDING: 1,
        Order.STATUS_CONFIRMED: 2,
        Order.STATUS_PROCESSING: 3,
        Order.STATUS_OUT_FOR_DELIVERY: 4,
        Order.STATUS_DELIVERED: 5,
        Order.STATUS_CANCELLED: 0,
    }
    current_step = status_order_map.get(order.status, 1)

    return render(request, 'orders/admin_order_detail.html', {
        'order': order,
        'milestones': milestones,
        'current_step': current_step,
        'status_choices': Order.STATUS_CHOICES,
        'title': f'Order #{order.order_number}',
    })
