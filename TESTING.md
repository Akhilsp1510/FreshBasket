# FreshBasket Testing Guide & Test Results

This document records the automated and manual test suite for the **FreshBasket** application.

---

## 1. Automated Test Suite Summary

- **Total Test Cases:** 8
- **Pass Rate:** 100% (8/8 Passed)
- **Execution Time:** ~9.5 seconds
- **Command to Run Tests:**
  ```powershell
  python manage.py test
  ```

---

## 2. Automated Test Cases Breakdown

| Test ID | Test Name | File | Purpose | Result |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | `test_single_successful_reservation` | `inventory/tests.py` | Validates reserving available stock, reducing available count, and creating an immutable `InventoryLog`. | **PASSED** |
| **TC-02** | `test_insufficient_stock_raises_error` | `inventory/tests.py` | Verifies that requesting more units than available raises `InsufficientStockError`. | **PASSED** |
| **TC-03** | `test_two_users_competing_sequential` | `inventory/tests.py` | **MVP 1 Central Innovation:** User A reserves the 1 remaining unit. User B attempts to reserve the same unit and is safely rejected. Available stock never goes negative. | **PASSED** |
| **TC-04** | `test_reservation_expiry_releases_stock` | `inventory/tests.py` | Verifies that when a reservation passes its 10-minute expiry time, `expire_reservations` releases the stock back to the shelf. | **PASSED** |
| **TC-05** | `test_low_stock_and_out_of_stock_alerts` | `inventory/tests.py` | **MVP 3:** Validates automatic trigger of Low-Stock and Out-of-Stock alerts, plus duplicate alert prevention. | **PASSED** |
| **TC-06** | `test_cart_addition_with_substitution_preference` | `orders/tests.py` | **MVP 4:** Validates storing customer substitution preference in the cart item. | **PASSED** |
| **TC-07** | `test_checkout_creates_order_and_deducts_inventory` | `orders/tests.py` | Validates checkout flow: converting cart to order, snapshotting prices, deducting physical stock, and creating audit logs. | **PASSED** |
| **TC-08** | `test_order_cancellation_restores_stock` | `orders/tests.py` | Validates that cancelling an eligible order automatically restores physical warehouse stock and logs the restoration. | **PASSED** |

---

## 3. Step-by-Step Manual Testing Scenarios (For College Viva & Demos)

### Scenario A: Customer Registration and Catalog Browsing
1. Open `http://127.0.0.1:8000/`.
2. Click **Register Free** &rarr; fill in name, email, password &rarr; Submit.
3. Expected: Account created, auto-logged in, welcome banner displayed with user's first name.
4. Go to **Products** page. Search for `"Milk"` or filter by `"Dairy & Eggs"`.
5. Expected: Filtered grid showing only milk items with real-time stock availability badges.

### Scenario B: The Two-Customers-One-Last-Unit Concurrency Test
1. As Admin, navigate to `/inventory/` and set the physical stock of `Britannia Bread` to **1 unit**.
2. Open **Window 1 (Chrome):** Log in as Customer 1 (`customer`).
3. Open **Window 2 (Incognito / Edge):** Log in as Customer 2 (`customer2`).
4. Both users navigate to `Britannia Bread` product detail page.
5. In Window 1, Customer 1 clicks **Add to Cart** and proceeds to **Checkout** &rarr; Clicks **Place Order**.
6. Immediately in Window 2, Customer 2 tries to proceed with checking out the same item.
7. **Expected Result:**
   - Customer 1: Order confirmed! Receives order number (e.g. `#FB1A2B3C`).
   - Customer 2: Friendly error: *"Only 0 unit(s) of Britannia Bread available. You requested 1."*
   - Admin Dashboard: Stock is 0, zero negative inventory, audit log records exactly one sale.

### Scenario C: Customer Substitution Preference Demonstration
1. Add `Amul Full Cream Milk` to cart.
2. In Cart, change the dropdown **If Unavailable** to *"Allow suitable substitute"*.
3. Complete checkout.
4. In **My Orders** &rarr; Click **View**, notice the substitution preference is permanently snapshotted in the order item.
5. In Admin Dashboard &rarr; Orders &rarr; click on the order, the store manager sees the customer's exact substitution instructions.

### Scenario D: Order Cancellation & Automatic Stock Restoration
1. Check available stock of `Tomatoes` in Admin Dashboard (e.g., 50 units).
2. Log in as `customer`, place an order for 5 units of `Tomatoes`.
3. Check stock in Admin Dashboard: physical stock is now 45 units.
4. As Customer, go to **My Orders** &rarr; click on the order &rarr; click **Cancel Order**.
5. Check stock in Admin Dashboard: physical stock is automatically restored to **50 units**.
6. Check **Inventory Audit Log**: A `cancellation` log entry is recorded with `+5` units restored!

