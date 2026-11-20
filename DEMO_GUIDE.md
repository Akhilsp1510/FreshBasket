# FreshBasket College Demonstration & Viva Presentation Guide

Follow this guide during your project demonstration to explain every feature confidently to your professor.

---

## 1. 30-Second Elevator Pitch

> *"Good morning Professor. My project is **FreshBasket: Design and Development of a Scalable Cloud-Based Grocery Ordering and Inventory-Consistency Management System Using Amazon Web Services**.*
>
> *In online grocery shopping, the biggest failure point is **inventory overselling**—when multiple customers buy the last item simultaneously, leading to delayed orders, refunds, and lost trust. FreshBasket solves this using **database row locking and transactional inventory reservations** combined with **AWS cloud infrastructure (EC2, RDS MySQL, and S3)**."*

---

## 2. 5-Minute Demonstration Script

### Step 1: Show the Homepage & Catalog (Customer View)
1. Open `http://127.0.0.1:8000/`.
2. Point out:
   - Modern, professional UI with fresh green brand identity (`#198754`).
   - Dynamic grocery categories with Bootstrap icons.
   - Featured products with real-time stock badges (`In Stock`, `Low Stock`, `Out of Stock`).
   - Search bar and category filters.

### Step 2: Demonstrate the 5 Core MVPs

#### MVP 1: Transaction-Safe Inventory Reservation
- Explain: *"When a customer adds an item and proceeds to checkout, FreshBasket uses `select_for_update()` in a database transaction to reserve the stock. If two customers try to buy the last unit at the same second, row locking forces one to wait, preventing overselling."*
- Demonstrate placing an order and watching stock decrement immediately.

#### MVP 2: Real-Time Product Availability
- Point out the dynamic badges:
  - Green `In Stock` (above low-stock threshold).
  - Yellow `Low Stock` (at or below threshold).
  - Red `Out of Stock` (button disabled).

#### MVP 3: Automatic Low-Stock & Out-of-Stock Alerts
- Switch to Admin Dashboard &rarr; **Alerts**.
- Show the automatic alert triggered when stock falls below the product's configurable threshold.
- Click **Acknowledge** to demonstrate the alert acknowledgment workflow.

#### MVP 4: Customer Substitution Preferences
- Show the Cart view with substitution preference options:
  - *Do not substitute*
  - *Allow suitable substitute*
  - *Use specific substitute*
- Explain how this handles stock discrepancies during order packing without cancelling the whole order.

#### MVP 5: Immutable Inventory Audit Trail
- Navigate to `/inventory/log/`.
- Show the complete history: timestamp, product name, change type (`restock`, `sale`, `reservation`, `cancellation`), quantity delta, before/after numbers, and actor.
- Emphasize: *"This audit log is append-only. It cannot be altered or deleted by any administrator, ensuring full accountability."*

### Step 3: Show the Admin Dashboard & Charts
- Navigate to `/dashboard/`.
- Show the interactive **Chart.js** charts: Orders by Status and Inventory Breakdown.
- Show the live database-driven statistics (Total Products, Total Orders, Physical Stock, Reserved Stock, Revenue).

### Step 4: Explain the AWS Cloud Architecture
- Open the architecture diagram from `ARCHITECTURE.md`.
- Explain how the application runs in production:
  - **EC2:** Hosts Django behind Gunicorn and Nginx reverse proxy.
  - **RDS:** Managed MySQL database isolated inside a private subnet.
  - **S3:** Cloud object storage for grocery product media.
  - **IAM:** Instance roles granting secure access without hardcoded API keys.
  - **CloudWatch:** Continuous logging and monitoring.

