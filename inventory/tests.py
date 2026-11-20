import threading
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from products.models import Category, Product
from inventory.models import Inventory, StockReservation, StockAlert, InventoryLog
from inventory.services import (
    reserve_stock, release_reservation, confirm_reservation,
    restock_product, expire_reservations, InsufficientStockError
)


class InventoryReservationTests(TransactionTestCase):
    """
    Tests MVP 1 (Transactional Reservation) and MVP 5 (Audit Trail).
    """

    def setUp(self):
        self.category = Category.objects.create(name='Dairy', slug='dairy')
        self.product = Product.objects.create(
            category=self.category,
            name='Test Milk',
            price=50.00,
            low_stock_threshold=5
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            physical_stock=1,
            reserved_stock=0
        )
        self.user_a = User.objects.create_user(username='user_a', password='Password123!')
        self.user_b = User.objects.create_user(username='user_b', password='Password123!')

    def test_single_successful_reservation(self):
        """User A can reserve 1 unit when 1 is available."""
        res = reserve_stock(self.user_a, self.product, 1)
        self.assertEqual(res.status, StockReservation.STATUS_ACTIVE)

        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.reserved_stock, 1)
        self.assertEqual(self.inventory.available_stock, 0)
        self.assertEqual(self.inventory.stock_status, Inventory.STATUS_OUT_OF_STOCK)

        # Audit log verification
        log = InventoryLog.objects.filter(product=self.product, change_type=InventoryLog.CHANGE_RESERVATION).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.quantity_changed, 1)
        self.assertEqual(log.performed_by, self.user_a)

    def test_insufficient_stock_raises_error(self):
        """Requesting more units than available raises InsufficientStockError."""
        with self.assertRaises(InsufficientStockError):
            reserve_stock(self.user_a, self.product, 5)

    def test_two_users_competing_sequential(self):
        """
        User A reserves the last unit. User B immediately attempts to reserve the same unit
        and is safely rejected with InsufficientStockError (no negative stock).
        """
        res_a = reserve_stock(self.user_a, self.product, 1)
        self.assertEqual(res_a.status, StockReservation.STATUS_ACTIVE)

        # User B tries to reserve the now-exhausted item
        with self.assertRaises(InsufficientStockError):
            reserve_stock(self.user_b, self.product, 1)

        # Stock must never be negative
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.physical_stock, 1)
        self.assertEqual(self.inventory.reserved_stock, 1)
        self.assertEqual(self.inventory.available_stock, 0)

    def test_reservation_expiry_releases_stock(self):
        """Expired reservations are cancelled and stock returns to available pool."""
        res = reserve_stock(self.user_a, self.product, 1)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.available_stock, 0)

        # Force the reservation expiry into the past
        res.expires_at = timezone.now() - timedelta(minutes=1)
        res.save()

        count = expire_reservations()
        self.assertEqual(count, 1)

        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.reserved_stock, 0)
        self.assertEqual(self.inventory.available_stock, 1)

        res.refresh_from_db()
        self.assertEqual(res.status, StockReservation.STATUS_CANCELLED)

    def test_low_stock_and_out_of_stock_alerts(self):
        """MVP 3: Alerts are generated when available stock hits thresholds."""
        # Restock to 10
        restock_product(self.product, 9, self.user_a, "Restock")
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.available_stock, 10)

        # Threshold is 5. Reserving 6 leaves 4 available -> Low Stock Alert!
        reserve_stock(self.user_a, self.product, 6)
        alert = StockAlert.objects.filter(product=self.product, alert_type=StockAlert.ALERT_LOW_STOCK).first()
        self.assertIsNotNone(alert)
        self.assertFalse(alert.is_acknowledged)

        # Duplicate alert prevention: calling check again should not create duplicate
        from inventory.services import _check_and_create_alert
        self.inventory.refresh_from_db()
        _check_and_create_alert(self.product, self.inventory)
        self.assertEqual(StockAlert.objects.filter(product=self.product, alert_type=StockAlert.ALERT_LOW_STOCK).count(), 1)

    def test_concurrent_reservation_multithreaded(self):
        """
        MVP 1 Concurrency: Two concurrent threads attempt to reserve the last unit
        simultaneously using separate database connections.
        Verify that exactly 1 succeeds, 1 fails with InsufficientStockError, and
        stock is never negative.
        """
        from django.db import connection
        outcomes = []
        lock = threading.Lock()

        def worker(user):
            connection.close()  # Force thread to open its own database connection
            try:
                res = reserve_stock(user, self.product, 1)
                with lock:
                    outcomes.append(('SUCCESS', res.id))
            except InsufficientStockError:
                with lock:
                    outcomes.append(('REJECTED', None))
            finally:
                connection.close()

        t1 = threading.Thread(target=worker, args=(self.user_a,))
        t2 = threading.Thread(target=worker, args=(self.user_b,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        successes = [o for o in outcomes if o[0] == 'SUCCESS']
        rejections = [o for o in outcomes if o[0] == 'REJECTED']
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(rejections), 1)

        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.physical_stock, 1)
        self.assertEqual(self.inventory.reserved_stock, 1)
        self.assertEqual(self.inventory.available_stock, 0)
