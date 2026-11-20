from django.db import models
from django.utils import timezone
from django.conf import settings


class Inventory(models.Model):
    """
    Single inventory record per product.
    physical_stock = actual items on shelf
    reserved_stock = items reserved in active checkouts (not yet purchased)
    available_stock = physical_stock - reserved_stock (what customers can still buy)
    """
    STATUS_IN_STOCK = 'in_stock'
    STATUS_LOW_STOCK = 'low_stock'
    STATUS_OUT_OF_STOCK = 'out_of_stock'
    STATUS_CHOICES = [
        (STATUS_IN_STOCK, 'In Stock'),
        (STATUS_LOW_STOCK, 'Low Stock'),
        (STATUS_OUT_OF_STOCK, 'Out of Stock'),
    ]

    product = models.OneToOneField(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    physical_stock = models.PositiveIntegerField(default=0)
    reserved_stock = models.PositiveIntegerField(default=0)
    stock_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OUT_OF_STOCK)
    last_restocked_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory'
        verbose_name_plural = 'Inventories'

    @property
    def available_stock(self):
        """Available stock = physical stock minus reserved stock."""
        return max(0, self.physical_stock - self.reserved_stock)

    def update_status(self):
        """Recalculate stock_status based on available stock."""
        threshold = self.product.low_stock_threshold
        if self.available_stock <= 0:
            self.stock_status = self.STATUS_OUT_OF_STOCK
        elif self.available_stock <= threshold:
            self.stock_status = self.STATUS_LOW_STOCK
        else:
            self.stock_status = self.STATUS_IN_STOCK

    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name}: {self.available_stock} available ({self.stock_status})"


class StockReservation(models.Model):
    """
    Temporarily holds stock for a customer during checkout.
    Expires after RESERVATION_EXPIRY_MINUTES minutes.
    This prevents overselling when multiple customers buy the last item.
    """
    STATUS_ACTIVE = 'active'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock_reservation'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expires_at', 'status']),
        ]

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Reservation: {self.user.username} - {self.product.name} x{self.quantity} ({self.status})"


class InventoryLog(models.Model):
    """
    Complete audit trail of every stock change.
    Every add, deduct, reserve, release is recorded here permanently.
    """
    CHANGE_RESTOCK = 'restock'
    CHANGE_SALE = 'sale'
    CHANGE_RESERVATION = 'reservation'
    CHANGE_RESERVATION_RELEASE = 'reservation_release'
    CHANGE_CANCELLATION = 'cancellation'
    CHANGE_CORRECTION = 'correction'
    CHANGE_SUBSTITUTION = 'substitution'
    CHANGE_TYPE_CHOICES = [
        (CHANGE_RESTOCK, 'Restock'),
        (CHANGE_SALE, 'Sale'),
        (CHANGE_RESERVATION, 'Reservation'),
        (CHANGE_RESERVATION_RELEASE, 'Reservation Release'),
        (CHANGE_CANCELLATION, 'Order Cancellation'),
        (CHANGE_CORRECTION, 'Manual Correction'),
        (CHANGE_SUBSTITUTION, 'Substitution'),
    ]

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='inventory_logs'
    )
    change_type = models.CharField(max_length=30, choices=CHANGE_TYPE_CHOICES)
    quantity_changed = models.IntegerField(help_text='Positive = added, Negative = deducted')
    previous_physical_stock = models.IntegerField()
    new_physical_stock = models.IntegerField()
    previous_reserved_stock = models.IntegerField()
    new_reserved_stock = models.IntegerField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_actions'
    )
    reason = models.CharField(max_length=500, blank=True)
    reference_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inventory_logs'
    )
    reference_reservation = models.ForeignKey(
        StockReservation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inventory_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_log'
        ordering = ['-timestamp']

    def __str__(self):
        direction = '+' if self.quantity_changed >= 0 else ''
        return f"{self.product.name}: {direction}{self.quantity_changed} ({self.change_type}) at {self.timestamp}"


class StockAlert(models.Model):
    """Low-stock and out-of-stock alerts for admin dashboard."""
    ALERT_LOW_STOCK = 'low_stock'
    ALERT_OUT_OF_STOCK = 'out_of_stock'
    ALERT_TYPE_CHOICES = [
        (ALERT_LOW_STOCK, 'Low Stock'),
        (ALERT_OUT_OF_STOCK, 'Out of Stock'),
    ]

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    stock_level_at_alert = models.IntegerField()
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_alert'
        ordering = ['-created_at']
        # Prevent duplicate active alerts for same product+type
        unique_together = []  # enforced in service layer

    def __str__(self):
        return f"[{self.alert_type}] {self.product.name} at {self.stock_level_at_alert} units"
