from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from products.models import Category, Product
from inventory.models import Inventory, InventoryLog
from orders.models import Cart, CartItem, Order, OrderItem
from inventory.services import restore_stock_on_cancellation


class OrderAndSubstitutionTests(TestCase):
    """
    Tests MVP 4 (Substitution Preferences) and Order Lifecycle with Stock Restoration.
    """

    def setUp(self):
        self.category = Category.objects.create(name='Snacks', slug='snacks')
        self.p1 = Product.objects.create(
            category=self.category,
            name='Potato Chips',
            price=20.00,
            low_stock_threshold=5
        )
        self.p2 = Product.objects.create(
            category=self.category,
            name='Banana Chips',
            price=25.00,
            low_stock_threshold=5
        )
        Inventory.objects.create(product=self.p1, physical_stock=20, reserved_stock=0)
        Inventory.objects.create(product=self.p2, physical_stock=15, reserved_stock=0)

        self.user = User.objects.create_user(username='shopper', password='Password123!', email='shopper@fb.in')
        self.client = Client()
        self.client.login(username='shopper', password='Password123!')

    def test_cart_addition_with_substitution_preference(self):
        """User can choose substitution preference when adding to cart."""
        url = reverse('orders:add_to_cart', args=[self.p1.id])
        response = self.client.post(url, {
            'quantity': 2,
            'substitution_preference': CartItem.SUBSTITUTE_ALLOW
        })
        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(user=self.user)
        item = cart.items.first()
        self.assertEqual(item.product, self.p1)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.substitution_preference, CartItem.SUBSTITUTE_ALLOW)

    def test_checkout_creates_order_and_deducts_inventory(self):
        """Checkout converts cart to order, deducts stock, and creates audit log."""
        # Add to cart
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.p1,
            quantity=3,
            substitution_preference=CartItem.SUBSTITUTE_ALLOW
        )

        checkout_url = reverse('orders:checkout')
        data = {
            'full_name': 'Test Shopper',
            'phone': '9876543210',
            'address_line1': '123 Market Road',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560001',
            'payment_method': 'cod',
            'notes': 'Please ring the bell'
        }
        response = self.client.post(checkout_url, data)
        self.assertEqual(response.status_code, 302)

        # Order created
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, 60.00 + 40.00) # 3 * 20 + 40 delivery fee

        # Physical stock deducted (was 20, now 17)
        inv = Inventory.objects.get(product=self.p1)
        self.assertEqual(inv.physical_stock, 17)
        self.assertEqual(inv.reserved_stock, 0)
        self.assertEqual(inv.available_stock, 17)

        # Audit log created
        log = InventoryLog.objects.filter(product=self.p1, change_type=InventoryLog.CHANGE_SALE).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.quantity_changed, -3)

    def test_order_cancellation_restores_stock(self):
        """Cancelling an order automatically returns the items to warehouse physical stock."""
        order = Order.objects.create(
            user=self.user,
            delivery_full_name='Test Shopper',
            delivery_phone='9876543210',
            delivery_address_line1='123 Market',
            delivery_city='Bengaluru',
            delivery_state='Karnataka',
            delivery_pincode='560001',
            status=Order.STATUS_PENDING
        )
        OrderItem.objects.create(
            order=order,
            product=self.p1,
            product_name=self.p1.name,
            product_price=self.p1.price,
            quantity=5
        )
        # Deduct initial 5 items for simulation
        inv = Inventory.objects.get(product=self.p1)
        inv.physical_stock = 15
        inv.save()

        # Cancel order
        restore_stock_on_cancellation(order, performed_by=self.user)
        inv.refresh_from_db()
        self.assertEqual(inv.physical_stock, 20) # Restored back from 15 to 20

        # Check cancellation audit log
        log = InventoryLog.objects.filter(product=self.p1, change_type=InventoryLog.CHANGE_CANCELLATION).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.quantity_changed, 5)
