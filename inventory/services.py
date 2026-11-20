"""
FreshBasket Inventory Service Layer
====================================
This file contains the core business logic for inventory management.
It handles the most critical feature: preventing overselling using database transactions.

KEY CONCEPTS:
- physical_stock  : Total items on the warehouse shelf
- reserved_stock  : Items held for active checkouts (not yet purchased)
- available_stock : physical_stock - reserved_stock  (what customers can still buy)

HOW OVERSELLING IS PREVENTED:
  select_for_update() LOCKS the database row during a transaction.
  If Customer A and Customer B both try to buy the last unit simultaneously:
    - A's transaction locks the row, checks stock (1 available), reserves it, commits
    - B's transaction waits → when it runs, stock is now 0 → raises InsufficientStockError
  Result: Only A succeeds. B sees a friendly "out of stock" message.
"""

import logging
from datetime import timedelta
from django.db import transaction
from django.db.utils import OperationalError
from django.utils import timezone
from django.conf import settings
from inventory.models import Inventory, StockReservation, InventoryLog, StockAlert
from products.models import Product

logger = logging.getLogger('inventory')


class InsufficientStockError(Exception):
    """Raised when there is not enough stock to fulfill a reservation."""
    pass


class ReservationError(Exception):
    """Raised when a reservation cannot be created for other reasons."""
    pass


def get_or_create_inventory(product):
    """Get or create an inventory record for a product."""
    inventory, created = Inventory.objects.get_or_create(
        product=product,
        defaults={'physical_stock': 0, 'reserved_stock': 0}
    )
    return inventory


def reserve_stock(user, product, quantity):
    """
    Reserve stock for a customer during checkout.

    Uses database transaction + select_for_update() to prevent race conditions.
    Returns the StockReservation object on success.
    Raises InsufficientStockError if not enough stock available or lock contention occurs.
    """
    expiry_minutes = getattr(settings, 'RESERVATION_EXPIRY_MINUTES', 10)

    try:
        with transaction.atomic():
            # Lock this inventory row — no other transaction can read/write until we commit
            try:
                inventory = Inventory.objects.select_for_update().get(product=product)
            except Inventory.DoesNotExist:
                raise InsufficientStockError(f"No inventory record found for {product.name}")

            # Cancel any existing active reservation by this user for this product
            existing = StockReservation.objects.filter(
                user=user,
                product=product,
                status=StockReservation.STATUS_ACTIVE
            ).first()

            if existing:
                inventory.reserved_stock = max(0, inventory.reserved_stock - existing.quantity)
                existing.status = StockReservation.STATUS_CANCELLED
                existing.save()

            # Check available stock
            available = inventory.physical_stock - inventory.reserved_stock

            if available < quantity:
                raise InsufficientStockError(
                    f"Only {available} unit(s) of '{product.name}' available. You requested {quantity}."
                )

            prev_physical = inventory.physical_stock
            prev_reserved = inventory.reserved_stock

            # Increase reserved stock
            inventory.reserved_stock += quantity
            inventory.save()

            reservation = StockReservation.objects.create(
                user=user,
                product=product,
                quantity=quantity,
                status=StockReservation.STATUS_ACTIVE,
                expires_at=timezone.now() + timedelta(minutes=expiry_minutes)
            )

            InventoryLog.objects.create(
                product=product,
                change_type=InventoryLog.CHANGE_RESERVATION,
                quantity_changed=quantity,
                previous_physical_stock=prev_physical,
                new_physical_stock=inventory.physical_stock,
                previous_reserved_stock=prev_reserved,
                new_reserved_stock=inventory.reserved_stock,
                performed_by=user,
                reason=f"Cart reservation for {quantity} unit(s)",
                reference_reservation=reservation
            )

            logger.info(
                f"Reserved {quantity} of {product.name} for user {user.username}. "
                f"Available now: {inventory.available_stock}"
            )

            _check_and_create_alert(product, inventory)
            return reservation
    except OperationalError:
        raise InsufficientStockError(
            f"The item '{product.name}' is currently being reserved by another customer. Please try again."
        )


def release_reservation(reservation, performed_by=None, reason="Reservation released"):
    """Release a reservation and return stock to the available pool."""
    with transaction.atomic():
        inventory = Inventory.objects.select_for_update().get(product=reservation.product)

        if reservation.status != StockReservation.STATUS_ACTIVE:
            logger.warning(f"Tried to release non-active reservation {reservation.id}")
            return

        prev_reserved = inventory.reserved_stock
        inventory.reserved_stock = max(0, inventory.reserved_stock - reservation.quantity)
        inventory.save()

        reservation.status = StockReservation.STATUS_CANCELLED
        reservation.save()

        InventoryLog.objects.create(
            product=reservation.product,
            change_type=InventoryLog.CHANGE_RESERVATION_RELEASE,
            quantity_changed=-reservation.quantity,
            previous_physical_stock=inventory.physical_stock,
            new_physical_stock=inventory.physical_stock,
            previous_reserved_stock=prev_reserved,
            new_reserved_stock=inventory.reserved_stock,
            performed_by=performed_by,
            reason=reason,
            reference_reservation=reservation
        )
        logger.info(f"Released reservation {reservation.id} for {reservation.product.name}")


def confirm_reservation(reservation, order):
    """
    Confirm a reservation when an order is placed.
    Deducts from physical_stock (item is sold) AND reduces reserved_stock
    (item is no longer just reserved — it is now permanently sold).
    """
    with transaction.atomic():
        inventory = Inventory.objects.select_for_update().get(product=reservation.product)

        prev_physical = inventory.physical_stock
        prev_reserved = inventory.reserved_stock

        inventory.physical_stock = max(0, inventory.physical_stock - reservation.quantity)
        inventory.reserved_stock = max(0, inventory.reserved_stock - reservation.quantity)
        inventory.save()

        reservation.status = StockReservation.STATUS_CONFIRMED
        reservation.save()

        InventoryLog.objects.create(
            product=reservation.product,
            change_type=InventoryLog.CHANGE_SALE,
            quantity_changed=-reservation.quantity,
            previous_physical_stock=prev_physical,
            new_physical_stock=inventory.physical_stock,
            previous_reserved_stock=prev_reserved,
            new_reserved_stock=inventory.reserved_stock,
            performed_by=reservation.user,
            reason=f"Sale confirmed via Order #{order.order_number}",
            reference_order=order,
            reference_reservation=reservation
        )
        logger.info(
            f"Confirmed sale of {reservation.quantity} {reservation.product.name} "
            f"in order {order.order_number}"
        )


def restore_stock_on_cancellation(order, performed_by=None):
    """Restore inventory when an order is cancelled."""
    with transaction.atomic():
        for item in order.items.all():
            try:
                inventory = Inventory.objects.select_for_update().get(product=item.product)
            except Inventory.DoesNotExist:
                continue
            prev_physical = inventory.physical_stock
            inventory.physical_stock += item.quantity
            inventory.save()

            InventoryLog.objects.create(
                product=item.product,
                change_type=InventoryLog.CHANGE_CANCELLATION,
                quantity_changed=item.quantity,
                previous_physical_stock=prev_physical,
                new_physical_stock=inventory.physical_stock,
                previous_reserved_stock=inventory.reserved_stock,
                new_reserved_stock=inventory.reserved_stock,
                performed_by=performed_by,
                reason=f"Stock restored: Order #{order.order_number} cancelled",
                reference_order=order
            )


def restock_product(product, quantity, performed_by, reason="Restock"):
    """Add stock to a product's physical inventory."""
    with transaction.atomic():
        inventory, _ = Inventory.objects.select_for_update().get_or_create(
            product=product,
            defaults={'physical_stock': 0, 'reserved_stock': 0}
        )
        prev_physical = inventory.physical_stock
        inventory.physical_stock += quantity
        inventory.last_restocked_at = timezone.now()
        inventory.save()

        InventoryLog.objects.create(
            product=product,
            change_type=InventoryLog.CHANGE_RESTOCK,
            quantity_changed=quantity,
            previous_physical_stock=prev_physical,
            new_physical_stock=inventory.physical_stock,
            previous_reserved_stock=inventory.reserved_stock,
            new_reserved_stock=inventory.reserved_stock,
            performed_by=performed_by,
            reason=reason
        )

        # Clear unacknowledged out-of-stock alerts if stock is now available
        if inventory.available_stock > 0:
            StockAlert.objects.filter(
                product=product, is_acknowledged=False
            ).update(is_acknowledged=True)

        return inventory


def expire_reservations():
    """
    Expire reservations older than RESERVATION_EXPIRY_MINUTES.
    Run this periodically via management command: python manage.py expire_reservations
    """
    expired = StockReservation.objects.filter(
        status=StockReservation.STATUS_ACTIVE,
        expires_at__lt=timezone.now()
    )
    count = 0
    for reservation in expired:
        try:
            release_reservation(reservation, reason="Reservation expired automatically")
            count += 1
        except Exception as e:
            logger.error(f"Failed to expire reservation {reservation.id}: {e}")
    if count:
        logger.info(f"Expired {count} reservation(s)")
    return count


def _check_and_create_alert(product, inventory):
    """Create low-stock or out-of-stock alert if needed. Prevents duplicate alerts."""
    available = inventory.available_stock
    threshold = product.low_stock_threshold

    if available <= 0:
        alert_type = StockAlert.ALERT_OUT_OF_STOCK
    elif available <= threshold:
        alert_type = StockAlert.ALERT_LOW_STOCK
    else:
        return  # Stock is fine

    exists = StockAlert.objects.filter(
        product=product,
        alert_type=alert_type,
        is_acknowledged=False
    ).exists()

    if not exists:
        StockAlert.objects.create(
            product=product,
            alert_type=alert_type,
            stock_level_at_alert=available
        )
        logger.warning(f"ALERT: {alert_type} for {product.name} (available: {available})")
