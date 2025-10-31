# Harvey Backend Migration to Azure VM

**Goal:** Move Harvey's backend from Replit to Azure VM (20.81.210.213) alongside the existing ML Prediction API.

**Timeline:** 2-3 hours for full migration with zero downtime

**Result:** Both services running on Azure VM with Nginx reverse proxy

---

## 🎯 Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  AZURE VM (20.81.210.213)                                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Nginx Reverse Proxy (Ports 80/443)                  │  │
│  │  - SSL/TLS via Let's Encrypt                         │  │
│  │  - Routes /api/* → Harvey Backend (localhost:8000)   │  │
│  │  - Routes /ml/* → ML API (localhost:9000)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────┐       ┌────────────────────────┐ │
│  │  Harvey Backend      │       │  ML Prediction API     │ │
│  │  Port: 8000          │       │  Port: 9000            │ │
│  │  (localhost only)    │       │  (localhost only)      │ │
│  │  Systemd: harvey.service     │  Systemd: ml-api.service │
│  └──────────────────────┘       └────────────────────────┘ │
│           ↓                               ↓                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Shared Resources                                     │  │
│  │  - Azure SQL Database (FreeTDS)                      │  │
│  │  - Azure Blob Storage (ML models)                    │  │
│  │  - Environment Variables (.env files)                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefits:**
- Both APIs on same VM → ML API calls via localhost (faster, no network overhead)
- Single SSL certificate for both services
- Unified monitoring and logging
- Lower latency for ML predictions (no external HTTP calls)
- Cost savings (one VM instead of Replit + Azure VM)

---

## 📋 Pre-Migration Checklist

### ✅ Prerequisites

- [x] Azure VM accessible via SSH (azureuser@20.81.210.213)
- [x] ML API already deployed on VM at /home/azureuser/ml-api/
- [x] Domain name configured (or using IP address)
- [ ] All Replit secrets documented
- [ ] Backup plan if migration fails

### 📦 What We're Migrating

**From Replit:**
- Harvey backend code (FastAPI app)
- Python dependencies (requirements.txt)
- Environment variables/secrets
- Database configurations (FreeTDS, ODBC)
- Background services (scheduler, cache prewarmer, ML health monitor)

**To Azure VM:**
- /opt/harvey-backend/ (application code)
- /opt/harvey-backend/.env (secrets)
- Systemd service for auto-restart
- Nginx configuration for reverse proxy

---

## 🚀 Migration Steps

### Phase 1: Prepare Azure VM Environment

#### Step 1.1: SSH into Azure VM

```bash
ssh azureuser@20.81.210.213
```

#### Step 1.2: Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python 3.11 and pip
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install FreeTDS and ODBC drivers (for Azure SQL)
sudo apt install -y freetds-dev freetds-bin unixodbc unixodbc-dev

# Install Nginx for reverse proxy
sudo apt install -y nginx

# Install certbot for SSL (optional, for HTTPS)
sudo apt install -y certbot python3-certbot-nginx

# Install Git for version control
sudo apt install -y git

# Install system monitoring tools
sudo apt install -y htop curl wget
```

#### Step 1.3: Configure FreeTDS for Azure SQL

```bash
# Create FreeTDS configuration
sudo tee /etc/freetds/freetds.conf > /dev/null <<EOF
[global]
tds version = 7.4
client charset = UTF-8

[AzureSQL]
host = <SQLSERVER_HOST>
port = 1433
tds version = 7.4
EOF
```

#### Step 1.4: Configure ODBC Driver

```bash
# Create ODBC driver configuration
sudo tee /etc/odbcinst.ini > /dev/null <<EOF
[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
EOF
```

---

### Phase 2: Deploy Harvey Backend Code

#### Step 2.1: Create Application Directory

```bash
# Create Harvey backend directory
sudo mkdir -p /opt/harvey-backend
sudo chown azureuser:azureuser /opt/harvey-backend
cd /opt/harvey-backend
```

#### Step 2.2: Transfer Harvey Code from Replit

**Option A: Using Git (Recommended)**

```bash
# If Harvey is in a Git repository
cd /opt/harvey-backend
git clone <YOUR_HARVEY_REPO_URL> .
```

**Option B: Using SCP from Your Local Machine**

```bash
# On your local machine (if you have Harvey code locally)
# Exclude unnecessary files
tar -czf harvey-backend.tar.gz \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pythonlibs' \
  harvey-backend/

# Transfer to Azure VM
scp harvey-backend.tar.gz azureuser@20.81.210.213:/tmp/

# On Azure VM
cd /opt/harvey-backend
tar -xzf /tmp/harvey-backend.tar.gz --strip-components=1
rm /tmp/harvey-backend.tar.gz
```

**Option C: Using Replit's Download Feature**

1. In Replit, download entire project as ZIP
2. Extract locally
3. Use SCP to transfer to Azure VM

#### Step 2.3: Create Python Virtual Environment

```bash
cd /opt/harvey-backend

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

#### Step 2.4: Install Python Dependencies

```bash
# Still in /opt/harvey-backend with venv activated
pip install -r requirements.txt

# Install additional system-level dependencies for pyodbc
pip install pyodbc
```

---

### Phase 3: Configure Environment & Secrets

#### Step 3.1: Create .env File

```bash
cd /opt/harvey-backend

# Create secure .env file
sudo tee .env > /dev/null <<EOF
# Harvey API Configuration
HARVEY_AI_API_KEY=<YOUR_HARVEY_AI_API_KEY>

# Azure SQL Database
SQLSERVER_HOST=<YOUR_SQLSERVER_HOST>
SQLSERVER_DB=<YOUR_SQLSERVER_DB>
SQLSERVER_USER=<YOUR_SQLSERVER_USER>
SQLSERVER_PASSWORD=<YOUR_SQLSERVER_PASSWORD>

# OpenAI API
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>

# ML API Configuration (LOCALHOST - both on same VM!)
ML_API_BASE_URL=http://127.0.0.1:9000/api/internal/ml
INTERNAL_ML_API_KEY=<YOUR_INTERNAL_ML_API_KEY>

# ODBC Configuration
ODBCSYSINI=/etc

# Environment
ENVIRONMENT=production
EOF

# Secure the .env file (only root and azureuser can read)
sudo chmod 600 .env
sudo chown azureuser:azureuser .env
```

**⚠️ IMPORTANT:** Replace all `<YOUR_*>` placeholders with actual values from Replit Secrets.

#### Step 3.2: Test Database Connection

```bash
# Still in /opt/harvey-backend with venv activated
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

import pyodbc

conn_str = (
    f\"DRIVER={{FreeTDS}};"
    f\"SERVER={os.getenv('SQLSERVER_HOST')};"
    f\"DATABASE={os.getenv('SQLSERVER_DB')};"
    f\"UID={os.getenv('SQLSERVER_USER')};"
    f\"PWD={os.getenv('SQLSERVER_PASSWORD')};"
    f\"TDS_Version=7.4;"
    f\"Port=1433;\"
)

try:
    conn = pyodbc.connect(conn_str)
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

**Expected:** `✅ Database connection successful!`

---

### Phase 4: Create Systemd Service for Harvey Backend

#### Step 4.1: Create Systemd Service File

```bash
sudo tee /etc/systemd/system/harvey.service > /dev/null <<EOF
[Unit]
Description=Harvey AI Financial Advisor Backend
After=network.target

[Service]
Type=simple
User=azureuser
Group=azureuser
WorkingDirectory=/opt/harvey-backend
Environment="PATH=/opt/harvey-backend/venv/bin"
Environment="ODBCSYSINI=/etc"
ExecStart=/opt/harvey-backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=append:/var/log/harvey/access.log
StandardError=append:/var/log/harvey/error.log

[Install]
WantedBy=multi-user.target
EOF
```

#### Step 4.2: Create Log Directory

```bash
sudo mkdir -p /var/log/harvey
sudo chown azureuser:azureuser /var/log/harvey
```

#### Step 4.3: Enable and Start Harvey Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable Harvey service to start on boot
sudo systemctl enable harvey.service

# Start Harvey service
sudo systemctl start harvey.service

# Check service status
sudo systemctl status harvey.service
```

**Expected output:**
```
● harvey.service - Harvey AI Financial Advisor Backend
   Loaded: loaded (/etc/systemd/system/harvey.service; enabled)
   Active: active (running) since ...
```

#### Step 4.4: Verify Harvey is Running

```bash
# Test Harvey backend health endpoint
curl http://127.0.0.1:8000/

# Check Harvey logs
sudo journalctl -u harvey.service -f
```

**Expected:** Harvey should respond with welcome message.

---

### Phase 5: Update ML API Configuration

#### Step 5.1: Update ML API to Listen on Localhost

```bash
cd /home/azureuser/ml-api

# Check current ML API startup command
# It should listen on 0.0.0.0:9000 currently
# Update it to 127.0.0.1:9000 for security (only accessible via Nginx)

# Edit the ML API startup script or systemd service
# Change: --host 0.0.0.0 --port 9000
# To:     --host 127.0.0.1 --port 9000
```

#### Step 5.2: Create/Update ML API Systemd Service

```bash
sudo tee /etc/systemd/system/ml-api.service > /dev/null <<EOF
[Unit]
Description=Harvey ML Prediction API
After=network.target

[Service]
Type=simple
User=azureuser
Group=azureuser
WorkingDirectory=/home/azureuser/ml-api
Environment="PATH=/home/azureuser/ml-api/venv/bin"
ExecStart=/home/azureuser/ml-api/venv/bin/uvicorn main:app --host 127.0.0.1 --port 9000 --workers 2
Restart=always
RestartSec=10
StandardOutput=append:/var/log/ml-api/access.log
StandardError=append:/var/log/ml-api/error.log

[Install]
WantedBy=multi-user.target
EOF
```

#### Step 5.3: Create ML API Log Directory

```bash
sudo mkdir -p /var/log/ml-api
sudo chown azureuser:azureuser /var/log/ml-api
```

#### Step 5.4: Enable and Restart ML API

```bash
sudo systemctl daemon-reload
sudo systemctl enable ml-api.service
sudo systemctl restart ml-api.service
sudo systemctl status ml-api.service
```

---

### Phase 6: Configure Nginx Reverse Proxy

#### Step 6.1: Create Nginx Configuration

```bash
sudo tee /etc/nginx/sites-available/harvey > /dev/null <<'EOF'
# Harvey Backend + ML API Reverse Proxy Configuration

upstream harvey_backend {
    server 127.0.0.1:8000;
}

upstream ml_api {
    server 127.0.0.1:9000;
}

server {
    listen 80;
    server_name 20.81.210.213;  # Replace with your domain if you have one

    # Increase timeouts for ML API (predictions can take time)
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;

    # Harvey Backend API (all routes except /ml/*)
    location / {
        proxy_pass http://harvey_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # CORS headers (if needed for frontend)
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
    }

    # ML API Routes
    location /api/internal/ml/ {
        proxy_pass http://ml_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /healthz {
        proxy_pass http://harvey_backend;
    }

    # ML Health endpoint
    location /v1/ml/health {
        proxy_pass http://harvey_backend;
    }

    # Increase client body size for file uploads
    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/harvey_access.log;
    error_log /var/log/nginx/harvey_error.log;
}
EOF
```

#### Step 6.2: Enable Nginx Configuration

```bash
# Create symlink to enable site
sudo ln -sf /etc/nginx/sites-available/harvey /etc/nginx/sites-enabled/

# Remove default Nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t
```

**Expected:** `nginx: configuration file /etc/nginx/nginx.conf test is successful`

#### Step 6.3: Restart Nginx

```bash
sudo systemctl restart nginx
sudo systemctl status nginx
```

---

### Phase 7: Configure Firewall (UFW)

#### Step 7.1: Set Up UFW Rules

```bash
# Enable UFW
sudo ufw --force enable

# Allow SSH (IMPORTANT - don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check UFW status
sudo ufw status numbered
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

**Note:** Port 9000 should NOT be in the firewall rules - it's only accessible via localhost.

---

### Phase 8: Configure Azure Network Security Group (NSG)

#### Step 8.1: Add Inbound Rules (Azure Portal)

1. Go to Azure Portal → Virtual Machines → Your VM
2. Click "Networking" → "Network settings"
3. Add inbound rules:

| Priority | Port | Protocol | Source | Description |
|----------|------|----------|--------|-------------|
| 1000 | 22 | TCP | Your IP | SSH access |
| 1010 | 80 | TCP | Any | HTTP |
| 1020 | 443 | TCP | Any | HTTPS |

**Remove or deny port 9000** - it should only be accessible via Nginx reverse proxy.

---

### Phase 9: Testing & Validation

#### Step 9.1: Test from Azure VM (Localhost)

```bash
# Test Harvey backend directly
curl http://127.0.0.1:8000/

# Test ML API directly
curl http://127.0.0.1:9000/health

# Test Harvey via Nginx
curl http://127.0.0.1/

# Test ML health via Harvey
curl http://127.0.0.1/v1/ml/health
```

#### Step 9.2: Test from External (Your Computer)

```bash
# Test Harvey backend
curl http://20.81.210.213/

# Test health endpoint
curl http://20.81.210.213/healthz

# Test ML health
curl http://20.81.210.213/v1/ml/health

# Test authenticated endpoint (replace with your API key)
curl -H "Authorization: Bearer YOUR_HARVEY_AI_API_KEY" \
  http://20.81.210.213/v1/chat \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top dividend stocks?"}'
```

#### Step 9.3: Check All Services Running

```bash
# On Azure VM
sudo systemctl status harvey.service
sudo systemctl status ml-api.service
sudo systemctl status nginx.service

# Check logs for errors
sudo journalctl -u harvey.service -n 50
sudo journalctl -u ml-api.service -n 50
sudo tail -f /var/log/nginx/harvey_error.log
```

---

### Phase 10: SSL/HTTPS Setup (Optional but Recommended)

#### Step 10.1: Obtain SSL Certificate (if you have a domain)

```bash
# Replace example.com with your actual domain
sudo certbot --nginx -d api.askheydividend.com

# Follow prompts to get free SSL certificate
```

#### Step 10.2: Auto-Renewal Setup

```bash
# Test auto-renewal
sudo certbot renew --dry-run

# Certbot automatically sets up cron job for renewal
```

---

## 🔄 Zero-Downtime Migration Strategy

### Option 1: DNS Cutover (If Using Domain)

1. **Keep Replit running** while deploying on Azure VM
2. **Deploy and test** everything on Azure VM
3. **Update DNS** to point to Azure VM IP (20.81.210.213)
4. **Monitor** traffic shifts from Replit to Azure VM
5. **Keep Replit as backup** for 48 hours
6. **Decommission Replit** after confirming stability

### Option 2: Direct Cutover (If Using IP/No Domain)

1. **Deploy on Azure VM** and test thoroughly
2. **Update frontend** to point to Azure VM IP
3. **Monitor logs** for errors
4. **Rollback to Replit** if issues detected

---

## 📊 Post-Migration Checklist

- [ ] Harvey backend responding on http://20.81.210.213/
- [ ] ML API accessible via Harvey at http://127.0.0.1:9000
- [ ] Database queries working (test dividend queries)
- [ ] Background services running (scheduler, cache prewarmer)
- [ ] ML Health Monitor showing circuit breaker closed
- [ ] SSL certificate installed (if using domain)
- [ ] Firewall rules configured (UFW + Azure NSG)
- [ ] Systemd services auto-start on reboot
- [ ] Logs rotating properly
- [ ] Frontend updated to point to new API endpoint

---

## 🔧 Monitoring & Maintenance

### Check Service Status

```bash
# Quick status check
sudo systemctl status harvey.service ml-api.service nginx.service

# View recent logs
sudo journalctl -u harvey.service -f
```

### Restart Services

```bash
# Restart Harvey backend
sudo systemctl restart harvey.service

# Restart ML API
sudo systemctl restart ml-api.service

# Restart Nginx
sudo systemctl restart nginx
```

### Update Code

```bash
cd /opt/harvey-backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart harvey.service
```

---

## 🚨 Rollback Plan

If migration fails:

1. **Keep Replit running** - don't stop it until Azure VM is proven stable
2. **Revert DNS** - point back to Replit (if using domain)
3. **Revert frontend** - point API calls back to Replit
4. **Debug Azure VM** - fix issues offline

---

## 💰 Cost Comparison

| Component | Before (Replit) | After (Azure VM) | Savings |
|-----------|-----------------|------------------|---------|
| Replit Hosting | $20-40/month | $0 | -$40/mo |
| Azure VM | $0 | $0 (already have) | $0 |
| Total Monthly | $101/month | $81.50/month | **-$20/mo** |

**Net Savings:** ~$20-40/month by consolidating to Azure VM.

---

## 📁 File Structure on Azure VM

```
/opt/harvey-backend/
├── venv/                   # Python virtual environment
├── app/                    # Harvey application code
├── main.py                 # FastAPI entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment secrets (chmod 600)
└── replit.md              # Documentation

/home/azureuser/ml-api/
├── venv/                   # ML API virtual environment
├── main.py                 # ML API entry point
└── models/                 # Downloaded from Azure Blob

/etc/nginx/sites-available/
└── harvey                  # Nginx reverse proxy config

/etc/systemd/system/
├── harvey.service          # Harvey systemd service
└── ml-api.service         # ML API systemd service

/var/log/
├── harvey/                 # Harvey logs
├── ml-api/                 # ML API logs
└── nginx/                  # Nginx logs
```

---

## 🎯 Next Steps After Migration

1. **Monitor for 48 hours** - ensure stability
2. **Set up monitoring** - Azure Monitor or similar
3. **Configure log rotation** - logrotate for /var/log/harvey
4. **Set up backups** - automated database backups
5. **Migrate secrets to Azure Key Vault** - more secure than .env files
6. **Configure auto-scaling** - if traffic grows
7. **Set up CI/CD** - GitHub Actions for automated deployments

---

**Ready to begin migration?** Start with Phase 1 and work through each step sequentially. Let me know if you need help with any specific phase! 🚀
