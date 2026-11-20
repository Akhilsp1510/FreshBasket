# FreshBasket Glossary: Beginner's Technical Dictionary

Welcome to the **FreshBasket Technical Glossary**. If you are new to programming, web development, or cloud computing, this dictionary explains every important concept in clear, everyday English without confusing jargon.

---

## 1. Core Web Concepts

### Frontend
- **What it means:** The visible part of the website that you see, touch, and click in your web browser.
- **In FreshBasket:** The HTML pages, green navigation bar, product cards, shopping cart, and admin dashboard charts built with Bootstrap 5 and JavaScript.

### Backend
- **What it means:** The behind-the-scenes engine that runs on a web server. It handles business logic, security, user passwords, calculations, and talks to the database.
- **In FreshBasket:** The Python code powered by the Django web framework that checks if items are in stock, verifies user logins, and processes orders.

### Server
- **What it means:** A computer (physical or virtual in the cloud) that listens for requests from web browsers 24/7 and sends back web pages or data.
- **In FreshBasket:** In local development, your own laptop runs the Django development server (`127.0.0.1:8000`). In production, an Amazon EC2 virtual server runs Gunicorn and Nginx.

### Client
- **What it means:** The device or browser (Chrome, Safari, Edge, or a mobile phone) used by a customer to visit a website.

### API (Application Programming Interface)
- **What it means:** A formal set of rules and endpoints allowing two computer programs to exchange messages with each other.
- **In FreshBasket:** The internal communication channels connecting the browser requests to Django views and AWS services.

---

## 2. Django & Python Concepts

### Django
- **What it means:** A high-level, batteries-included Python web framework designed to help developers build secure and maintainable websites quickly.
- **In FreshBasket:** Django manages our URL routing, user authentication, HTML rendering, database operations, and admin dashboard.

### ORM (Object-Relational Mapping)
- **What it means:** A translator that lets developers interact with a SQL database using Python objects and methods instead of writing raw SQL queries.
- **Example in FreshBasket:** Instead of writing `SELECT * FROM product WHERE is_active = 1;`, you write `Product.objects.filter(is_active=True)`.

### Migration
- **What it means:** Python blueprints that tell Django how to create or alter tables in the database to match your Python model classes.
- **Command:** `python manage.py makemigrations` (creates the blueprint) followed by `python manage.py migrate` (executes the blueprint on the database).

### Model
- **What it means:** A Python class that defines the structure and data types of a database table (e.g. `User`, `Product`, `Inventory`, `Order`).

### View
- **What it means:** A Python function in Django that receives a web request from a user, performs the required actions, and returns an HTTP response (such as rendering an HTML page).

### Template
- **What it means:** An HTML file enriched with Django template tags (e.g. `{{ product.name }}` or `{% for item in items %}`) that displays dynamic data to the user.

### Virtual Environment (venv)
- **What it means:** An isolated directory on your computer containing a specific version of Python and its installed libraries, preventing conflicts with other projects.

### Environment Variable (.env)
- **What it means:** Key-value pairs stored outside the application code to hold sensitive configuration details (passwords, secret keys, database URLs, AWS credentials) so they are never exposed in Git repositories.

---

## 3. Database & Concurrency Concepts

### Relational Database (RDBMS)
- **What it means:** A database system that organizes data into structured tables with rows and columns, linked together by relationships (Foreign Keys).
- **In FreshBasket:** MySQL (or Amazon RDS MySQL) stores all products, users, inventory levels, orders, and audit logs.

### Primary Key (PK)
- **What it means:** A unique identifier for each record in a database table (typically an auto-incrementing integer like `id = 1, 2, 3...`).

### Foreign Key (FK)
- **What it means:** A field in one table that points directly to the Primary Key of another table, creating a relational connection.
- **Example:** In the `Order` and `OrderItem` tables, `order_id` links each ordered grocery item to its parent order.

### Database Transaction
- **What it means:** A group of database operations executed as a single, indivisible unit of work. Either all operations succeed (Commit), or if any part fails, everything is undone (Rollback).
- **Rule:** ACID (Atomicity, Consistency, Isolation, Durability).

### Row Locking (`select_for_update`)
- **What it means:** A database mechanism where a transaction locks a specific table row until it finishes updating it. Other transactions attempting to modify that row must wait.
- **In FreshBasket:** Used in `reserve_stock()` to guarantee that two customers cannot purchase the last unit simultaneously.

### Physical Stock
- **What it means:** The physical quantity of items physically sitting on the grocery store shelves.

### Reserved Stock
- **What it means:** The quantity of items currently locked in active customer checkouts but not yet finalized as paid orders.

### Available Stock
- **Formula:** `available_stock = physical_stock - reserved_stock`.
- **Significance:** The real-time quantity that other shoppers are allowed to purchase.

### Race Condition / Overselling
- **What it means:** A concurrency bug that occurs when two parallel requests check stock simultaneously, both see 1 unit available, and both place an order, resulting in selling 2 items when only 1 exists. FreshBasket completely eliminates this via database row locks.

---

## 4. Amazon Web Services (AWS) Concepts

### Cloud Computing
- **What it means:** Delivering computing services (servers, storage, databases, networking, software) over the Internet on a pay-as-you-go pricing model instead of buying physical hardware.

### Amazon EC2 (Elastic Compute Cloud)
- **What it means:** Resizable virtual computing servers hosted in Amazon's data centers.
- **In FreshBasket:** An EC2 instance running Ubuntu Linux hosts our Django application, Gunicorn WSGI server, and Nginx web server.

### Amazon RDS (Relational Database Service)
- **What it means:** A fully managed database service that automates database setup, patching, backups, and failure recovery.
- **In FreshBasket:** RDS runs our managed MySQL database in a secure private subnet.

### Amazon S3 (Simple Storage Service)
- **What it means:** Highly scalable, high-speed, secure cloud object storage.
- **In FreshBasket:** S3 securely stores uploaded grocery product images and media files.

### AWS IAM (Identity and Access Management)
- **What it means:** A security service that controls who can sign in (authentication) and what AWS resources they have permission to use (authorization).
- **In FreshBasket:** We use IAM Roles attached to EC2 so the server can write images to S3 without embedding secret API keys in the code.

### Amazon VPC (Virtual Private Cloud)
- **What it means:** A logically isolated virtual network within AWS dedicated to your AWS account, mirroring a traditional on-premises data center.
- **In FreshBasket:** EC2 sits in a public subnet to receive web traffic, while RDS sits in an isolated private subnet with no direct Internet access for security.

### Security Group
- **What it means:** A virtual firewall that controls inbound and outbound network traffic for your EC2 instances and RDS databases.

### Amazon CloudWatch
- **What it means:** A monitoring and observability service that collects CPU metrics, memory usage, network health, and application logs.
- **In FreshBasket:** CloudWatch monitors application server performance and low-stock event logs.

---

## 5. Security & Authentication Concepts

### Authentication
- **What it means:** Verifying *who you are* (e.g. entering your username and password to log into your account).

### Authorization
- **What it means:** Verifying *what you are allowed to do* (e.g. verifying that a customer cannot view the admin dashboard or edit product prices).

### CSRF (Cross-Site Request Forgery)
- **What it means:** An attack where an unauthorized site tricks a logged-in user into submitting malicious requests.
- **Protection in FreshBasket:** Django automatically injects a hidden `{% csrf_token %}` into every HTML form to verify origin authenticity.

### Password Hashing
- **What it means:** Transforming a plaintext password into a cryptographically scrambled string using algorithms like PBKDF2 with SHA-256 and salts. Plaintext passwords are never stored in the database.

