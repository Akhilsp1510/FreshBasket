from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Grocery product categories (Fruits, Vegetables, Dairy, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Bootstrap icon name e.g. bi-apple')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_product_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    """Individual grocery products."""
    UNIT_KG = 'kg'
    UNIT_G = 'g'
    UNIT_L = 'L'
    UNIT_ML = 'ml'
    UNIT_PCS = 'pcs'
    UNIT_PACK = 'pack'
    UNIT_DOZEN = 'dozen'
    UNIT_CHOICES = [
        (UNIT_KG, 'Kilogram'),
        (UNIT_G, 'Gram'),
        (UNIT_L, 'Litre'),
        (UNIT_ML, 'Millilitre'),
        (UNIT_PCS, 'Pieces'),
        (UNIT_PACK, 'Pack'),
        (UNIT_DOZEN, 'Dozen'),
    ]
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default=UNIT_KG)
    unit_quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    low_stock_threshold = models.PositiveIntegerField(default=10, help_text='Alert when stock falls below this')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product'
        ordering = ['name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_display_price(self):
        return f"₹{self.price}"

    @property
    def mrp(self):
        """Simulated MRP for realistic Blinkit strike-through price display."""
        from decimal import Decimal
        return round(self.price * Decimal('1.15'))

    @property
    def discount_percent(self):
        """Discount percentage."""
        if self.mrp > self.price:
            return round(((self.mrp - self.price) / self.mrp) * 100)
        return 0

    @property
    def unit_display(self):
        """Friendly unit label like '1 kg', '500 ml', '12 pcs'"""
        qty = int(self.unit_quantity) if self.unit_quantity == int(self.unit_quantity) else self.unit_quantity
        return f"{qty} {self.unit}"

    @property
    def rating(self):
        """Simulated customer rating (4.6 to 4.9)."""
        ratings = [4.7, 4.8, 4.9, 4.6, 4.8, 4.7]
        return ratings[self.pk % len(ratings)]

    @property
    def review_count(self):
        """Simulated review count."""
        return 40 + (self.pk * 7) % 180

    def get_inventory(self):
        try:
            return self.inventory
        except Exception:
            return None

    def get_available_stock(self):
        inv = self.get_inventory()
        if inv:
            return inv.available_stock
        return 0

    def get_stock_status(self):
        inv = self.get_inventory()
        if not inv:
            return 'out_of_stock'
        return inv.stock_status


class SubstituteGroup(models.Model):
    """Groups of substitute products."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'substitute_group'

    def __str__(self):
        return self.name


class SubstituteGroupItem(models.Model):
    """Products belonging to a substitute group."""
    group = models.ForeignKey(SubstituteGroup, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='substitute_groups')
    priority = models.PositiveIntegerField(default=1, help_text='Lower = preferred substitute')

    class Meta:
        db_table = 'substitute_group_item'
        unique_together = ('group', 'product')
        ordering = ['priority']

    def __str__(self):
        return f"{self.group.name} - {self.product.name}"
