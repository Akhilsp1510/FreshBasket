# FreshBasket AWS Cloud Deployment Manual

This guide provides **step-by-step, copy-paste-ready instructions** to deploy the FreshBasket Django web application onto Amazon Web Services (AWS) using an affordable, Free-Tier eligible architecture.

---

## 1. Cloud Architecture Overview

| AWS Service | Role in FreshBasket | Configuration Details |
| :--- | :--- | :--- |
| **Amazon EC2** | Application Server | Ubuntu 24.04 LTS (t2.micro / t3.micro), Nginx, Gunicorn |
| **Amazon RDS** | Managed MySQL Database | db.t3.micro / db.t4g.micro, Multi-AZ (optional), Private Subnet |
| **Amazon S3** | Product Image Storage | S3 Standard Bucket with public-read permissions for media |
| **AWS IAM** | Security & Access | EC2 Instance Role with `AmazonS3FullAccess` and CloudWatch access |
| **Amazon VPC** | Network Isolation | Custom or Default VPC with Public & Private Subnets |
| **CloudWatch** | Logging & Alarms | Application logs and EC2 CPU / Disk monitoring |

---

## 2. Step 1: Create an Amazon S3 Bucket for Product Media

1. Open the [AWS Management Console](https://console.aws.amazon.com/) and search for **S3**.
2. Click **Create bucket**.
3. **Bucket name:** Enter a unique name, e.g., `freshbasket-media-yourname` (lowercase, numbers, and hyphens only).
4. **AWS Region:** Choose `ap-south-1` (Asia Pacific - Mumbai) or your nearest region.
5. **Block Public Access settings:**
   - Uncheck *Block all public access*.
   - Check the acknowledgement box stating you know objects will be accessible publicly.
6. Click **Create bucket**.
7. Go into your newly created bucket &rarr; Click **Permissions** tab &rarr; Scroll to **Bucket Policy** &rarr; Click **Edit**:
   Paste the following JSON (replace `freshbasket-media-yourname` with your actual bucket name):
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "PublicReadGetObject",
               "Effect": "Allow",
               "Principal": "*",
               "Action": "s3:GetObject",
               "Resource": "arn:aws:s3:::freshbasket-media-yourname/*"
           }
       ]
   }
   ```
8. Click **Save changes**.

---

## 3. Step 2: Create an IAM Instance Role for EC2

Instead of saving AWS secret keys on the server, we attach an **IAM Role** directly to our EC2 instance:
1. In the AWS Console, search for **IAM**.
2. In the left sidebar, click **Roles** &rarr; **Create role**.
3. **Trusted entity type:** Select **AWS service**.
4. **Use case:** Choose **EC2**. Click **Next**.
5. **Permissions policies:** Search and select:
   - `AmazonS3FullAccess`
   - `CloudWatchAgentServerPolicy`
6. Click **Next**.
7. **Role name:** Enter `FreshBasketEC2Role`.
8. Click **Create role**.

---

## 4. Step 3: Launch Amazon RDS MySQL Database

1. In the AWS Console, search for **RDS**.
2. Click **Create database**.
3. Choose **Standard create**.
4. **Engine type:** Select **MySQL** (version 8.0.x).
5. **Templates:** Select **Free Tier**.
6. **DB instance identifier:** `freshbasket-db`.
7. **Credentials Settings:**
   - Master username: `admin`
   - Master password: Enter a strong password (e.g. `FreshBasketPass2024!`) and save it securely!
8. **DB instance class:** `db.t3.micro` or `db.t4g.micro` (Free-tier eligible).
9. **Storage:** General Purpose SSD (gp2), 20 GiB. Uncheck *Enable storage autoscaling*.
10. **Connectivity:**
    - Virtual Private Cloud (VPC): Choose your default VPC.
    - Public access: Select **No** (best cloud security practice: EC2 will talk to RDS internally).
    - VPC security group: Choose **Create new**, name it `rds-mysql-sg`.
11. **Initial database name:** Scroll down to *Additional configuration* &rarr; Enter `freshbasket_db`.
12. Click **Create database**. Wait 5–10 minutes until status turns to **Available**.
13. Once available, click on the database name and copy the **Endpoint** (e.g. `freshbasket-db.cxxxx.ap-south-1.rds.amazonaws.com`).

---

## 5. Step 4: Configure Security Groups

1. Go to **EC2** &rarr; **Security Groups**.
2. **EC2 Security Group (`ec2-web-sg`):**
   - Inbound Rules:
     - SSH (Port 22): My IP (your home IP).
     - HTTP (Port 80): Anywhere IPv4 (`0.0.0.0/0`).
     - HTTPS (Port 443): Anywhere IPv4 (`0.0.0.0/0`).
3. **RDS Security Group (`rds-mysql-sg`):**
   - Click *Edit inbound rules*.
   - Add rule: Type: **MYSQL/Aurora** (Port 3306), Source: Select `ec2-web-sg` (the security group of your EC2 instance).
   - This ensures **only** your EC2 web server can access your database.

---

## 6. Step 5: Launch & Connect to Amazon EC2 Instance

1. In the AWS Console, search for **EC2** &rarr; Click **Launch instance**.
2. **Name:** `FreshBasket-WebServer`.
3. **AMI:** Choose **Ubuntu Server 24.04 LTS (HVM), SSD Volume Type**.
4. **Instance type:** `t2.micro` (or `t3.micro` in regions where t2 isn't free-tier).
5. **Key pair:** Choose **Create new key pair** &rarr; Name it `freshbasket-key` &rarr; Key pair type: RSA &rarr; Private key file format: `.pem` (for Mac/Linux/OpenSSH) or `.ppk` (for PuTTY). Download and save it safely.
6. **Network settings:**
   - Auto-assign public IP: **Enable**.
   - Select existing security group: `ec2-web-sg`.
7. **Advanced details:**
   - IAM instance profile: Select `FreshBasketEC2Role`.
8. Click **Launch instance**.

### Connect to EC2 via SSH (Windows PowerShell / Mac Terminal):
```powershell
# In PowerShell (navigate to folder with freshbasket-key.pem)
ssh -i "freshbasket-key.pem" ubuntu@<YOUR-EC2-PUBLIC-IP>
```

---

## 7. Step 6: Server Setup & Application Deployment

Once connected to your Ubuntu EC2 terminal, run these commands:

### 1. Update OS and Install Prerequisites
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx pkg-config default-libmysqlclient-dev build-essential
```

### 2. Clone the Project Repository
```bash
cd /home/ubuntu
git clone https://github.com/<YOUR-GITHUB-USERNAME>/FreshBasket.git
cd FreshBasket
```

### 3. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Production Environment Variables (`.env`)
Create the `.env` file on the server:
```bash
nano .env
```
Paste your production settings:
```ini
DEBUG=False
SECRET_KEY=generate-a-strong-random-50-character-string-here
ALLOWED_HOSTS=<YOUR-EC2-PUBLIC-IP>,<YOUR-DOMAIN-NAME>,localhost

# Database (Amazon RDS MySQL)
DB_ENGINE=mysql
USE_RDS=True
DB_NAME=freshbasket_db
DB_USER=admin
DB_PASSWORD=<YOUR-RDS-MASTER-PASSWORD>
DB_HOST=<YOUR-RDS-ENDPOINT>
DB_PORT=3306

# AWS S3 Storage
USE_S3=True
AWS_STORAGE_BUCKET_NAME=freshbasket-media-yourname
AWS_S3_REGION_NAME=ap-south-1
```
Press `Ctrl+O`, `Enter`, then `Ctrl+X` to save and exit.

### 5. Run Migrations & Load Data on RDS
```bash
python manage.py migrate
python manage.py seed_data
python manage.py create_demo_users
python manage.py collectstatic --noinput
```

---

## 8. Step 7: Configure Gunicorn and Nginx

### 1. Create Gunicorn Systemd Service
```bash
sudo nano /etc/systemd/system/gunicorn.service
```
Paste this configuration:
```ini
[Unit]
Description=Gunicorn daemon for FreshBasket Django Project
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/FreshBasket
ExecStart=/home/ubuntu/FreshBasket/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          freshbasket.wsgi:application

[Install]
WantedBy=multi-user.target
```
Enable and start Gunicorn:
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

### 2. Configure Nginx Reverse Proxy
```bash
sudo nano /etc/nginx/sites-available/freshbasket
```
Paste this configuration:
```nginx
server {
    listen 80;
    server_name <YOUR-EC2-PUBLIC-IP>;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /home/ubuntu/FreshBasket;
    }

    location /media/ {
        root /home/ubuntu/FreshBasket;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```
Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/freshbasket /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## 9. Step 8: Setup Automatic Expiry Cron Job

On the EC2 server, configure a cron job to expire stale stock reservations every minute:
```bash
crontab -e
```
Add this line at the bottom:
```cron
* * * * * /home/ubuntu/FreshBasket/venv/bin/python /home/ubuntu/FreshBasket/manage.py expire_reservations >> /home/ubuntu/FreshBasket/reservation_cron.log 2>&1
```
Save and exit.

---

## 10. Step 9: Verify Live Deployment

Open your browser and navigate to:
```
http://<YOUR-EC2-PUBLIC-IP>/
```
You will see the live, production FreshBasket grocery shopping website running directly on AWS!

