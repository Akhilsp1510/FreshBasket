# FreshBasket – AWS Cloud Deployment & Infrastructure Readiness Guide

> **Project:** FreshBasket – Cloud-Based Grocery Ordering & Inventory Management System  
> **Target Cloud Provider:** Amazon Web Services (AWS)  
> **Target AWS Region:** Asia Pacific (Mumbai) — `ap-south-1`  
> **Architecture Model:** 3-Tier Web Architecture (Free-Tier Eligible)  
> **Audience:** College Capstone Project — Designed for Beginners & Evaluators

---

## 1. Cloud Architecture Overview

FreshBasket utilizes a robust, production-standard 3-tier cloud architecture hosted entirely within the AWS Mumbai (`ap-south-1`) region.

```
                  ┌────────────────────────────────────────┐
                  │          End User / Web Browser         │
                  └───────────────┬──────────────┬─────────┘
                                  │              │
                   HTTP/HTTPS     │              │ Static Media
                   Port 80/443    │              │ (Product Images)
                                  ▼              ▼
                  ┌──────────────────────┐ ┌───────────────┐
                  │    Amazon EC2        │ │   Amazon S3   │
                  │  (Ubuntu 24.04 LTS)  │ │ (Media Bucket)│
                  │                      │ └───────▲───────┘
                  │  ┌────────────────┐  │         │
                  │  │ Nginx (Reverse)│  │         │ IAM Instance Role
                  │  └───────┬────────┘  │         │ (No hardcoded keys)
                  │          ▼           │         │
                  │  ┌────────────────┐  │         │
                  │  │ Gunicorn (WSGI)│──┼─────────┘
                  │  └───────┬────────┘  │
                  │          ▼           │
                  │  ┌────────────────┐  │
                  │  │ Django 6.0 App │  │
                  │  └────────────────┘  │
                  └──────────┬───────────┘
                             │
                             │ MySQL Protocol (Port 3306)
                             │ Internal VPC Only (Private)
                             ▼
                  ┌──────────────────────┐
                  │   Amazon RDS MySQL   │
                  │ (Single-AZ Free Tier)│
                  │ Database: freshbasket│
                  └──────────────────────┘
```

---

## 2. AWS Services & Their Specific Roles

| AWS Service | Exact Role in FreshBasket | Configuration & Tier Specs |
| :--- | :--- | :--- |
| **Amazon EC2** *(Compute)* | Runs the Ubuntu Linux operating system, Gunicorn application server, Nginx web server, and Django application code. | `t2.micro` or `t3.micro` (1 vCPU, 1 GB RAM, 20 GB gp3 storage). Free Tier: 750 hours/month. |
| **Amazon RDS MySQL** *(Database)* | Managed relational database storing products, user accounts, orders, inventory logs, and stock reservations. | MySQL 8.0 on `db.t3.micro` or `db.t4g.micro` (20 GB gp2/gp3 storage). Free Tier: 750 hours/month. |
| **Amazon S3** *(Object Storage)* | Scalable cloud bucket storing high-resolution grocery product and category photography. Offloads media traffic from EC2. | S3 Standard in `ap-south-1`. Free Tier: 5 GB standard storage, 20,000 GET requests. |
| **AWS IAM** *(Security)* | Manages permissions. An **IAM EC2 Instance Role** grants the EC2 instance permission to read/write to S3 without storing AWS keys in files. | Principle of Least Privilege: S3 full access scoped to project bucket + CloudWatch logging. |
| **Amazon VPC & Security Groups** *(Networking)* | Virtual isolated network. Uses security groups as virtual firewalls to isolate the database from the public Internet. | Public subnet for EC2; RDS security group only allows inbound traffic from EC2's security group. |
| **Nginx & Gunicorn** *(Web Stack)* | Gunicorn executes Python/Django WSGI processes. Nginx acts as a high-speed reverse proxy handling client requests and caching static files. | Gunicorn bound to Unix socket `/run/gunicorn.sock`. Nginx listens on Port 80/443. |

---

## 3. How the Services Connect (Communication Flow)

1. **Client to EC2:** A customer or store manager visits `http://<EC2-IP>/` in their browser. Traffic arrives at EC2 on Port 80 (HTTP) or Port 443 (HTTPS).
2. **Nginx Reverse Proxy:** Nginx receives the request.
   - For `/static/` assets (CSS, UI icons): Nginx serves them immediately from local disk or WhiteNoise.
   - For application routes (login, product catalog, checkout): Nginx proxies the request across a local UNIX socket (`/run/gunicorn.sock`) to Gunicorn.
3. **Django Application Processing:** Gunicorn forwards the request to Django's WSGI application handler.
4. **EC2 to RDS MySQL (Database Connection):**
   - When Django queries products, user sessions, or stock reservations, it connects over private VPC networking to the Amazon RDS MySQL endpoint on Port 3306.
   - **Crucial Security:** The RDS instance has `Public Accessibility = No`. Only the EC2 instance can reach it.
5. **EC2 to S3 (Media Storage via IAM Role):**
   - When an administrator uploads a new product image, Django uses `boto3` and `django-storages` to push the file to the S3 bucket.
   - No AWS Access Keys are stored in the `.env` file on the server. The EC2 instance automatically authenticates using its attached IAM Role (`FreshBasketEC2Role`).
6. **S3 to Client (Image Delivery):**
   - When users browse the grocery catalog, product images load directly from the public S3 URL (`https://freshbasket-media-xxxx.s3.ap-south-1.amazonaws.com/media/...`), lightening the server load.

---

## 4. Beginner-Friendly AWS Setup Checklist (Phase 3.0)

Follow this checklist step-by-step before provisioning any servers:

### A. AWS Account Creation & Root Protection
- [ ] **1. Sign Up / Sign In:** Create or log in to your account at [https://aws.amazon.com/](https://aws.amazon.com/).
- [ ] **2. Enable Root MFA (Mandatory for Security):**
  - Go to the top-right menu &rarr; **Security credentials**.
  - Under **Multi-factor authentication (MFA)**, click **Assign MFA device**.
  - Choose **Authenticator app** (Google Authenticator, Microsoft Authenticator, or 1Password).
  - Scan the QR code with your mobile phone, enter two consecutive 6-digit codes, and activate.
- [ ] **3. Create an IAM Admin User (Do Not Use Root Daily):**
  - Search for **IAM** in the top search bar &rarr; Click **Users** &rarr; **Create user**.
  - User name: `freshbasket-admin`.
  - Check: *Provide user access to the AWS Management Console*.
  - Attach policy directly: `AdministratorAccess`.
  - Save credentials and log in as this IAM user for all project work.

### B. AWS Region Selection
- [ ] **4. Select the Mumbai Region:**
  - Look at the top-right navbar next to your account name.
  - Click the dropdown and select **Asia Pacific (Mumbai) `ap-south-1`**.
  - **Why?** Lowest latency for Indian users, localized compliance, and full Free Tier support for EC2, RDS, and S3.

### C. Cost Control & Zero-Surprise Billing Safeguards
- [ ] **5. Create an AWS Zero-Spend Budget:**
  - Search for **AWS Budgets** in the top search bar &rarr; Click **Create budget**.
  - Choose **Zero spend budget** (Template).
  - Enter your email address to receive immediate alerts the moment your account exceeds $0.01.
- [ ] **6. Enable Free Tier Usage Alerts:**
  - Open **Billing and Cost Management** &rarr; In left menu, click **Billing preferences**.
  - Check: *Receive Free Tier Usage Alerts*.
  - Enter your notification email address &rarr; Click **Update**.
- [ ] **7. Understand the AWS Free Tier Limits:**
  - **EC2:** 750 free hours/month of `t2.micro` or `t3.micro` (enough to run 1 instance 24/7 all month).
  - **RDS:** 750 free hours/month of Single-AZ `db.t3.micro` or `db.t4g.micro` with 20 GB storage.
  - **S3:** 5 GB of standard storage, 20,000 GET requests, 2,000 PUT requests.
  - *Keep strictly within these instance types to stay 100% free.*

### D. Security Architecture Rules
- [ ] **8. Never Expose RDS to the Public Internet:**
  - Set `Public access: No` during RDS creation.
  - The database must only be accessible from the EC2 security group on Port 3306.
- [ ] **9. Use IAM Roles Instead of Long-Lived Access Keys:**
  - Never generate or hardcode permanent `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` on the EC2 server.
  - Instead, attach an EC2 Instance Profile (`FreshBasketEC2Role`) with `AmazonS3FullAccess`.

---

## 5. Deployment Sequence Roadmap

The deployment of FreshBasket to AWS follows an organized phase-by-phase progression:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 3.0: Infrastructure Planning & Account Readiness (CURRENT)       │
│ • Validate Django codebase, requirements, and settings.                 │
│ • Secure AWS account with MFA, Mumbai region, and Zero-Spend Budget.   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 3.1: Cloud Storage & Security Foundations (NEXT)                 │
│ • Create Amazon S3 Bucket: freshbasket-media-<unique-id> in ap-south-1. │
│ • Configure S3 Public Read Bucket Policy for product images.            │
│ • Create IAM Role: FreshBasketEC2Role with S3 & CloudWatch access.      │
│ • Define VPC Security Groups: ec2-web-sg and rds-mysql-sg.              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 3.2: Managed Database Provisioning (Amazon RDS)                   │
│ • Launch MySQL 8.0 db.t3.micro instance (Single-AZ, Free Tier).        │
│ • Set database name: freshbasket_db.                                    │
│ • Restrict incoming Port 3306 exclusively to ec2-web-sg.                 │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 3.3: Web Server Provisioning & Application Launch (Amazon EC2)    │
│ • Launch Ubuntu 24.04 LTS t2.micro/t3.micro with FreshBasketEC2Role.    │
│ • Install Python 3.12/3.13, Nginx, libmysqlclient-dev.                  │
│ • Clone GitHub repository & create Python virtual environment.          │
│ • Configure server .env with RDS endpoint and S3 bucket details.        │
│ • Execute migrations, seed grocery catalog, and collect static files.   │
│ • Configure Gunicorn systemd service and Nginx reverse proxy.           │
│ • Setup cron job for 10-minute reservation expiry.                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 3.4: Live Verification & Capstone Evaluation                     │
│ • Test customer checkout, live inventory counters, and admin ledger.   │
│ • Verify image rendering directly from Amazon S3.                       │
│ • Prepare resource cleanup protocol post-demonstration.                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Expected Production Configuration Variables (Placeholders)

When configuring the production `.env` file on the EC2 server, only placeholder templates should be used during preparation:

```ini
# ==============================================================================
# FRESHBASKET PRODUCTION ENVIRONMENT CONFIGURATION (AWS EC2)
# ==============================================================================

# Core Django Security
DEBUG=False
SECRET_KEY=<GENERATE_50_CHAR_RANDOM_SECRET_KEY>
ALLOWED_HOSTS=<YOUR_EC2_PUBLIC_IP>,<YOUR_DOMAIN_NAME_OR_ALB>,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://<YOUR_EC2_PUBLIC_IP>,https://<YOUR_EC2_PUBLIC_IP>

# Database Configuration (Amazon RDS MySQL)
DB_ENGINE=mysql
USE_RDS=True
DB_NAME=freshbasket_db
DB_USER=admin
DB_PASSWORD=<YOUR_STRONG_RDS_MASTER_PASSWORD>
DB_HOST=<YOUR_RDS_ENDPOINT_e.g._freshbasket-db.cxxxxx.ap-south-1.rds.amazonaws.com>
DB_PORT=3306

# Amazon S3 Media Storage
USE_S3=True
AWS_STORAGE_BUCKET_NAME=<YOUR_UNIQUE_S3_BUCKET_NAME>
AWS_S3_REGION_NAME=ap-south-1
# Note: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are omitted because 
# EC2 uses the attached IAM Instance Profile (FreshBasketEC2Role).

# Production SSL & Reverse Proxy (Enabled when Domain/ALB is attached)
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=31536000
```

---

## 7. Cost Control, Resource Management & Cleanup

Because this is an academic project, preventing unexpected AWS charges is essential.

### While Developing & Testing
1. **Never launch more than 1 EC2 instance or 1 RDS instance.** The AWS Free Tier provides 750 hours per month for each, which equals exactly 31.25 days of 24/7 continuous operation for a single instance.
2. **Never select Multi-AZ for RDS** or Provisioned IOPS (io1/io2), as these exceed the Free Tier.
3. **If you take a break for a week:** You can stop the EC2 instance from the AWS console (Actions &rarr; Instance state &rarr; Stop). *Note: Stopping RDS is temporary (AWS restarts it after 7 days).*

### Post-Capstone Project Teardown (Complete Cleanup)
Once college evaluation and viva examinations are completed, delete all cloud resources to ensure zero ongoing costs:
1. **EC2:** Select `FreshBasket-WebServer` &rarr; Instance state &rarr; **Terminate instance**.
2. **RDS:** Select `freshbasket-db` &rarr; Actions &rarr; **Delete** (Uncheck *Create final snapshot*, check *I acknowledge*).
3. **S3:** Open your bucket &rarr; Click **Empty** (delete all objects) &rarr; Click **Delete bucket**.
4. **IAM:** Delete `FreshBasketEC2Role` and `freshbasket-admin` if you no longer need them.
5. **Security Groups:** Delete `ec2-web-sg` and `rds-mysql-sg`.
