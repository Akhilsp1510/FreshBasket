# FreshBasket: Design and Development of a Scalable Cloud-Based Grocery Ordering and Inventory-Consistency Management System Using Amazon Web Services

**Academic Project Report**

---

## Abstract

Online grocery retailing is characterized by fast-moving perishable inventory, high order volumes, and thin profit margins. A critical challenge faced by online grocery platforms is inventory overselling, which occurs when multiple concurrent customer sessions attempt to purchase the final available units of limited stock simultaneously. In conventional web architectures, concurrent read-check-write operations without strict concurrency controls result in race conditions, negative inventory, cancelled orders, and diminished customer trust.

This project presents **FreshBasket**, an end-to-end full-stack cloud-based grocery ordering and inventory management system designed and developed using Python, Django, MySQL, and Amazon Web Services (AWS). FreshBasket introduces a transactional inventory reservation engine utilizing database-level row locking (`SELECT ... FOR UPDATE`) and atomic transaction blocks to eliminate race conditions and guarantee ACID compliance during concurrent checkouts. The system features a responsive, customer-centric grocery web application, an administrative metrics dashboard with interactive telemetry, automated low-stock alert pipelines, customizable customer substitution preferences, and an immutable audit ledger. In production, FreshBasket is engineered for deployment on AWS using Amazon EC2 for computing, Amazon RDS MySQL for managed private database storage, Amazon S3 for cloud object storage, IAM instance profiles for least-privilege security, and Amazon CloudWatch for observability.

---

## 1. Introduction & Problem Statement

### 1.1 Existing Systems and Limitations
Traditional online shopping platforms often decouple inventory deduction from order initiation. In typical implementations:
1. Customer A reads stock level: `1 unit`.
2. Customer B reads stock level: `1 unit`.
3. Customer A places order: stock decreases to `0`.
4. Customer B places order: stock decreases to `-1` (Overselling!).

When this occurs, fulfillment centers cannot pack the promised goods. The store must cancel orders, issue refunds, and manage customer disappointment.

### 1.2 Proposed System
FreshBasket resolves this fundamental inconsistency by introducing a **Two-Phase Inventory Commitment Protocol**:
- **Phase 1 (Reservation):** When a customer enters the checkout pipeline, stock is reserved using `SELECT ... FOR UPDATE` with an automated 10-minute expiry window.
- **Phase 2 (Confirmation / Rollback):** Upon order placement, the reservation converts into a confirmed sale and physical inventory is deducted. If the transaction is abandoned or expires, the reservation is cancelled and units return to the available pool.

---

## 2. Technology Stack & Design

| Tier | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6), Bootstrap 5, Bootstrap Icons, Chart.js |
| **Backend** | Python 3.13, Django 6.0, Django ORM, Django Authentication, WhiteNoise |
| **Database** | MySQL 8.0 (Local Development & Amazon RDS in Production) |
| **Cloud (AWS)** | Amazon EC2, Amazon RDS, Amazon S3, AWS IAM, Amazon VPC, Amazon CloudWatch |

---

## 3. The Five Core MVP Features

1. **Transactional Inventory Reservation (MVP 1):** Eliminates race conditions and prevents negative stock through row-level locking.
2. **Real-Time Product Availability (MVP 2):** Calculates dynamic availability (`physical_stock - reserved_stock`) and renders visual status badges.
3. **Low-Stock and Out-of-Stock Alerts (MVP 3):** Automatically alerts administrators when stock dips below product-specific thresholds.
4. **Customer Substitution Preferences (MVP 4):** Enables customers to choose replacement preferences for perishable items.
5. **Inventory Audit Ledger & Admin Analytics (MVP 5):** Immutable, permanent audit trail recording every inventory state transition.

---

## 4. Experimental Results & Verification

Automated concurrency test suites were executed to validate transaction safety under load. During high-contention simulation where parallel requests targeted the last available unit of stock, the database row-locking mechanism successfully serialized the requests. Exactly one request succeeded, while competing requests were safely rejected with `InsufficientStockError`, preventing overselling and ensuring zero negative inventory across all test iterations.

---

## 5. Conclusion & Future Scope

FreshBasket successfully demonstrates an intermediate college-level cloud computing and web architecture project. Future enhancements may include:
- Multi-store warehouse routing.
- Real-time customer push notifications using WebSockets and Django Channels.
- Machine-learning driven predictive replenishment forecasting based on seasonal consumption patterns.

