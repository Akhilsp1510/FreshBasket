# FreshBasket System & AWS Cloud Architecture

**FreshBasket: Design and Development of a Scalable Cloud-Based Grocery Ordering and Inventory-Consistency Management System Using Amazon Web Services**

---

## 1. Architectural Overview

FreshBasket follows a modern **three-tier web architecture**:

1. **Presentation Tier (Frontend):** HTML5, CSS3, Bootstrap 5, responsive layouts, dynamic stock badges, and Chart.js dashboards.
2. **Application Tier (Backend):** Python 3.13, Django 6.0, Django ORM, custom authentication, and transaction-safe inventory reservation services.
3. **Data Tier (Storage & Cloud):** MySQL (or Amazon RDS MySQL) for relational transactional data, and Amazon S3 for cloud object storage.

---

## 2. High-Level System Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer["1. Client Layer"]
        Browser["Customer Browser / Mobile Device"]
        AdminBrowser["Store Administrator Browser"]
    end

    subgraph InternetLayer["2. Internet & Security"]
        HTTPS["HTTPS Requests (Port 443 / Port 80)"]
        Firewall["Security Group Firewall"]
    end

    subgraph AppTier["3. Application Tier (Amazon EC2)"]
        Nginx["Nginx Reverse Proxy / Web Server"]
        Gunicorn["Gunicorn WSGI Application Server"]
        DjangoApp["FreshBasket Django 6.0 Core"]
        
        subgraph DjangoServices["Django Service Layer"]
            AccountsSvc["Accounts & Auth Service"]
            CatalogSvc["Product Catalog Service"]
            InventorySvc["Transactional Inventory Service (select_for_update)"]
            OrderSvc["Order & Checkout Processing"]
            DashboardSvc["Admin Metrics Engine"]
        end
    end

    subgraph StorageTier["4. Data & Cloud Storage Tier"]
        RDS["Amazon RDS MySQL Database (Private Subnet)"]
        S3["Amazon S3 Bucket (Product Images)"]
        CloudWatch["Amazon CloudWatch (Logs & Metrics)"]
    end

    Browser --> HTTPS
    AdminBrowser --> HTTPS
    HTTPS --> Firewall
    Firewall --> Nginx
    Nginx --> Gunicorn
    Gunicorn --> DjangoApp
    
    DjangoApp --> AccountsSvc
    DjangoApp --> CatalogSvc
    DjangoApp --> InventorySvc
    DjangoApp --> OrderSvc
    DjangoApp --> DashboardSvc

    DjangoServices -->|SQL Queries & Transactions| RDS
    DjangoServices -->|Direct Upload / Presigned URLs| S3
    DjangoServices -->|Application Logs & Heartbeats| CloudWatch
```

---

## 3. AWS Cloud Network Infrastructure (VPC & Subnets)

To ensure enterprise-grade security and intermediate college-level cloud best practices:
- The **Amazon EC2 application server** is placed inside a **Public Subnet** with an Internet Gateway so that shoppers can visit the website.
- The **Amazon RDS MySQL database** is placed inside an isolated **Private Subnet** with **NO direct Internet access**. It only accepts incoming traffic on port 3306 from the EC2 security group.

```mermaid
flowchart LR
    subgraph AWSVPC["Amazon Virtual Private Cloud (VPC: 10.0.0.0/16)"]
        subgraph PublicSubnet["Public Subnet (10.0.1.0/24)"]
            IGW["Internet Gateway"]
            EC2Instance["Amazon EC2 Ubuntu Server<br>Nginx + Gunicorn + Django<br>(Elastic IP)"]
        end

        subgraph PrivateSubnet["Private Database Subnet (10.0.2.0/24)"]
            RDSInstance["Amazon RDS MySQL<br>(Port 3306 - No Public IP)"]
        end
    end

    UserInternet(("World Wide Web / Customers")) -->|Port 80/443| IGW
    IGW --> EC2Instance
    EC2Instance -->|Internal VPC Traffic Port 3306| RDSInstance
    EC2Instance -.->|IAM Instance Role| AWSS3[("Amazon S3 Bucket")]
    EC2Instance -.->|Metrics & Alarms| AWSCloudWatch[("AWS CloudWatch")]
```

---

## 4. Concurrency & Transactional Flow (MVP 1 Core Innovation)

The central innovation of FreshBasket is preventing inventory overselling. The sequence diagram below demonstrates how `select_for_update()` serializes concurrent requests to maintain inventory consistency:

```mermaid
sequenceDiagram
    autonumber
    actor Alice as Customer A
    actor Bob as Customer B
    participant Django as FreshBasket Backend
    participant DB as MySQL Database (Inventory Table)

    Note over Alice,Bob: Warehouse Physical Stock = 1 unit
    Alice->>Django: Checkout item (Request 1 unit)
    Bob->>Django: Checkout item (Request 1 unit)

    activate Django
    Django->>DB: BEGIN TRANSACTION (Alice)
    Django->>DB: SELECT * FROM inventory WHERE product_id=1 FOR UPDATE;
    Note over DB: ROW IS LOCKED for Alice!

    Django-->>DB: BEGIN TRANSACTION (Bob)
    Django-->>DB: SELECT * FROM inventory WHERE product_id=1 FOR UPDATE;
    Note over DB: Bob's query pauses and waits for lock release...

    Django->>DB: Available stock = 1 >= 1. Reserve 1 unit.
    Django->>DB: UPDATE inventory SET reserved_stock = 1;
    Django->>DB: INSERT INTO stock_reservation (status='active', expires_in=10m);
    Django->>DB: COMMIT (Alice)
    Note over DB: Lock released for Alice!
    Django-->>Alice: Reservation Successful! (Proceed to Checkout)

    Note over DB: Bob's query now acquires the lock!
    DB->>Django: Returns locked row to Bob: physical=1, reserved=1
    Django->>Django: Available stock = 1 - 1 = 0 unit!
    Django->>DB: ROLLBACK (Bob)
    Django-->>Bob: 400 Out of Stock / Insufficient stock error!
    deactivate Django

    Note over Alice,Bob: Result: Only Alice bought the item. Zero overselling!
```

---

## 5. Security Architecture

1. **Role-Based Access Control (RBAC):** Custom `User` model with strict separation between `customer` and `admin` roles, enforced via `@require_admin` decorators on all management views.
2. **Safe Credential Management:** Zero hardcoded keys. Database credentials, Django secrets, and AWS region configurations are read from `.env` via `python-dotenv`.
3. **Database Injection Protection:** 100% of queries use Django ORM parameterized queries; raw SQL concatenation is strictly forbidden.
4. **Cross-Site Request Forgery (CSRF):** Form tokens validated on every `POST` request.
5. **Session Isolation:** HTTP-only cookies and automatic session timeouts protect customer privacy.

