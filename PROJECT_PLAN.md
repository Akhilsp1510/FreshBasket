# FreshBasket Project Plan & Milestone Tracking

**Project Title:** FreshBasket: Design and Development of a Scalable Cloud-Based Grocery Ordering and Inventory-Consistency Management System Using Amazon Web Services.

**Target Duration:** 3–4 Weeks (Intermediate College Level Cloud Project)

---

## 1. Development Phases & Checklist

### Phase 0: Workspace Setup & Architecture (Complete)
- [x] Inspect workspace and check Python / environment tools.
- [x] Define requirements, technology stack, and beginner guidelines.
- [x] Create project documentation (`README.md`, `ARCHITECTURE.md`, `GLOSSARY.md`, `DATABASE_DESIGN.md`).
- [x] Scaffold Django project with 5 modular apps (`accounts`, `products`, `inventory`, `orders`, `dashboard`).

### Phase 1: Frontend User Experience & UI/UX (Complete)
- [x] Design brand identity: Fresh green theme (`#198754`), clean typography, rounded cards.
- [x] Build reusable Bootstrap 5 template hierarchy (`base.html`, `base_dashboard.html`).
- [x] Build Customer Views: Homepage, Product Catalog, Product Detail, Cart, Checkout, Order Confirmation, Order History, Customer Profile, Address Management.
- [x] Build Admin Views: Statistics Dashboard with Chart.js, Product Management, Category Management, Inventory Table, Restocking Modal, Alerts Management, Immutable Audit Ledger.

### Phase 2: Backend Architecture & Data Models (Complete)
- [x] Implement extended `User` and `Address` models.
- [x] Implement `Category`, `Product`, `SubstituteGroup`, and `SubstituteGroupItem` models.
- [x] Implement `Inventory`, `StockReservation`, `StockAlert`, and `InventoryLog` models.
- [x] Implement `Cart`, `CartItem`, `Order`, `OrderItem`, and `Payment` models.
- [x] Create and execute initial database migrations (`0001_initial.py`).
- [x] Develop idempotent `seed_data` management command (8 categories, 32 realistic grocery items).
- [x] Develop `create_demo_users` command for instant college viva login.

### Phase 3: The Five Core MVPs (Complete)
- [x] **MVP 1: Transactional Inventory Reservation**
  - Database row-locking via `select_for_update()`.
  - Atomic transactions with auto-rollback on insufficient stock.
  - 10-minute expiry management command (`expire_reservations`).
- [x] **MVP 2: Real-Time Product Availability**
  - Dynamic `available_stock = physical_stock - reserved_stock`.
  - Color-coded badges (`In Stock`, `Low Stock`, `Out of Stock`).
- [x] **MVP 3: Low-Stock & Out-of-Stock Alerts**
  - Configurable threshold triggers.
  - Alert deduplication and administrative acknowledgment flow.
- [x] **MVP 4: Customer Substitution Preferences**
  - Selection: "No substitute", "Allow suitable substitute", or "Specific product".
  - Historical snapshot preserved in `OrderItem`.
- [x] **MVP 5: Inventory Audit Trail & Admin Dashboard**
  - Read-only historical ledger capturing every stock transition.
  - Interactive charts for order status and inventory breakdown.

### Phase 4: AWS Cloud Integration Readiness (Complete)
- [x] Configure Amazon S3 settings for product image uploads (`django-storages` + `boto3`).
- [x] Configure Amazon RDS MySQL connectivity via `.env` parameterization.
- [x] Design IAM least-privilege EC2 role policies.
- [x] Setup CloudWatch logging formats and monitoring plan.

### Phase 5: Verification & Quality Assurance (Complete)
- [x] Automated Django test suite verifying all 5 MVPs (`inventory/tests.py`, `orders/tests.py`).
- [x] Concurrency protection tests verifying prevention of negative inventory.
- [x] Order cancellation and automatic inventory restoration verification.

### Phase 6: Final Demonstration & Academic Documentation (Complete)
- [x] Create comprehensive textbook-style `README.md`.
- [x] Create step-by-step `DEMO_GUIDE.md` for professor evaluation.
- [x] Create detailed `AWS_DEPLOYMENT.md` copy-paste execution manual.
- [x] Create formal academic `PROJECT_REPORT.md`.

