from django.db import models
from django.conf import settings
from decimal import Decimal


class Cart(models.Model):
    """Shopping cart for a user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart'

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    """Individual item in a shopping cart."""
    SUBSTITUTE_ALLOW = 'allow'
    SUBSTITUTE_SPECIFIC = 'specific'
    SUBSTITUTE_NONE = 'none'
    SUBSTITUTE_CHOICES = [
        (SUBSTITUTE_ALLOW, 'Allow any suitable substitute'),
        (SUBSTITUTE_SPECIFIC, 'Use specific substitute'),
        (SUBSTITUTE_NONE, 'Do not substitute'),
    ]

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    substitution_preference = models.CharField(
        max_length=20,
        choices=SUBSTITUTE_CHOICES,
        default=SUBSTITUTE_NONE
    )
    specific_substitute = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='substitute_cart_items'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_item'
        unique_together = ('cart', 'product')

    def get_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class Order(models.Model):
    """A placed order."""
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PROCESSING = 'processing'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_OUT_FOR_DELIVERY, 'Out for Delivery'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    PAYMENT_COD = 'cod'
    PAYMENT_SIMULATED = 'simulated'
    PAYMENT_CHOICES = [
        (PAYMENT_COD, 'Cash on Delivery'),
        (PAYMENT_SIMULATED, 'Online Payment (Simulated)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_COD)
    payment_status = models.CharField(max_length=20, default='pending')

    # Delivery address snapshot (stored at order time, not linked to Address)
    delivery_full_name = models.CharField(max_length=100)
    delivery_phone = models.CharField(max_length=15)
    delivery_address_line1 = models.CharField(max_length=255)
    delivery_address_line2 = models.CharField(max_length=255, blank=True)
    delivery_city = models.CharField(max_length=100)
    delivery_state = models.CharField(max_length=100)
    delivery_pincode = models.CharField(max_length=10)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('40.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"FB{uuid.uuid4().hex[:8].upper()}"
        self.total_amount = self.subtotal + self.delivery_fee
        super().save(*args, **kwargs)

    def can_cancel(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED]

    def __str__(self):
        return f"Order #{self.order_number} by {self.user.username}"


class OrderItem(models.Model):
    """Individual item in a placed order. Prices are snapshotted at order time."""
    SUBSTITUTE_ALLOW = 'allow'
    SUBSTITUTE_SPECIFIC = 'specific'
    SUBSTITUTE_NONE = 'none'
    SUBSTITUTE_CHOICES = [
        (SUBSTITUTE_ALLOW, 'Allow any suitable substitute'),
        (SUBSTITUTE_SPECIFIC, 'Use specific substitute'),
        (SUBSTITUTE_NONE, 'Do not substitute'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    # Price snapshot - preserves the price at time of purchase
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    substitution_preference = models.CharField(
        max_length=20,
        choices=SUBSTITUTE_CHOICES,
        default=SUBSTITUTE_NONE
    )
    substitute_product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='substituted_in_orders'
    )
    substitute_name = models.CharField(max_length=200, blank=True)
    substitute_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'order_item'

    def get_subtotal(self):
        price = self.substitute_price if self.substitute_product else self.product_price
        return price * self.quantity

    def __str__(self):
        return f"{self.product_name} x{self.quantity} in Order #{self.order.order_number}"


class Payment(models.Model):
    """Payment record for an order."""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment'

    def __str__(self):
        return f"Payment for Order #{self.order.order_number}: ₹{self.amount} ({self.status})"
