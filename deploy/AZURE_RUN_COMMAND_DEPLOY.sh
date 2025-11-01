#!/bin/bash
# Harvey Backend - Azure Run Command Deployment
# Run this script through Azure Portal → VM → Run Command
# NO SSH REQUIRED! NO FILE UPLOADS REQUIRED!

set -e

echo "=========================================="
echo "Harvey Backend - Azure Run Command Deploy"
echo "=========================================="
echo ""

# ============================================
# STEP 1: EDIT YOUR SECRETS HERE
# ============================================
# IMPORTANT: Add your OPENAI_API_KEY below (currently empty)
# All other secrets are pre-filled from Replit environment

HARVEY_AI_API_KEY=hd_live_abc123xyz789
SQLSERVER_HOST=hey-dividend-sql-server.database.windows.net
SQLSERVER_DB=HeyDividend-Main-DB
SQLSERVER_USER=Hey-dividend
SQLSERVER_PASSWORD=qUrkac-medqe7-sixvis
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY_HERE>
ML_API_BASE_URL=http://20.81.210.213:9000/api/internal/ml
INTERNAL_ML_API_KEY=hd_live_2r7TVaWMQ9q4QEjGE_internal_ml_api_key
PDFCO_API_KEY=dev@heydividend.com_z7X3c3xEvoPZHfonkI1Xr7Rq4ujl3XWb1jMUhbKjEgQPMu4OWc1XBZFo4kITEPMN

# ============================================
# STEP 2: System Setup
# ============================================

echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    freetds-dev \
    freetds-bin \
    unixodbc \
    unixodbc-dev \
    nginx \
    git \
    curl \
    wget \
    htop

echo "✅ Dependencies installed"

# ============================================
# STEP 3: Configure FreeTDS and ODBC
# ============================================

echo "🔧 Configuring database drivers..."

cat > /etc/freetds/freetds.conf <<'EOF'
[global]
tds version = 7.4
client charset = UTF-8
EOF

cat > /etc/odbcinst.ini <<'EOF'
[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
EOF

echo "✅ Database drivers configured"

# ============================================
# STEP 4: Clone Harvey from GitHub
# ============================================

echo "📁 Cloning Harvey backend from GitHub..."

# Remove old installation if exists
rm -rf /opt/harvey-backend

# Clone the repository
cd /opt
git clone https://github.com/heydividend/llm-server.git harvey-backend

cd /opt/harvey-backend

echo "✅ Harvey repository cloned"

# ============================================
# STEP 5: Create Environment File
# ============================================

echo "📝 Creating .env file with secrets..."

# Create .env file with secrets
cat > /opt/harvey-backend/.env <<EOF
HARVEY_AI_API_KEY=$HARVEY_AI_API_KEY
SQLSERVER_HOST=$SQLSERVER_HOST
SQLSERVER_DB=$SQLSERVER_DB
SQLSERVER_USER=$SQLSERVER_USER
SQLSERVER_PASSWORD=$SQLSERVER_PASSWORD
OPENAI_API_KEY=$OPENAI_API_KEY
ML_API_BASE_URL=http://127.0.0.1:9000/api/internal/ml
INTERNAL_ML_API_KEY=$INTERNAL_ML_API_KEY
PDFCO_API_KEY=$PDFCO_API_KEY
ODBCSYSINI=/etc
ENVIRONMENT=production
EOF

chmod 600 /opt/harvey-backend/.env
chown -R azureuser:azureuser /opt/harvey-backend

# Create log directories
mkdir -p /var/log/harvey /var/log/ml-api
chown -R azureuser:azureuser /var/log/harvey /var/log/ml-api

echo "✅ Environment configured"

# ============================================
# STEP 6: Create Python Virtual Environment
# ============================================

echo "🐍 Creating Python virtual environment..."

cd /opt/harvey-backend
sudo -u azureuser python3.11 -m venv venv
sudo -u azureuser /opt/harvey-backend/venv/bin/pip install --upgrade pip
sudo -u azureuser /opt/harvey-backend/venv/bin/pip install -r requirements.txt

echo "✅ Virtual environment created and dependencies installed"

# ============================================
# STEP 7: Create Systemd Services
# ============================================

echo "🔧 Creating systemd services..."

# Harvey service
cat > /etc/systemd/system/harvey.service <<'EOF'
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

# ML API service (if exists)
if [ -d "/home/azureuser/ml-api" ]; then
cat > /etc/systemd/system/ml-api.service <<'EOF'
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
fi

echo "✅ Systemd services created"

# ============================================
# STEP 8: Configure Nginx
# ============================================

echo "🌐 Configuring Nginx reverse proxy..."

cat > /etc/nginx/sites-available/harvey <<'EOF'
upstream harvey_backend { server 127.0.0.1:8000; }
upstream ml_api { server 127.0.0.1:9000; }

server {
    listen 80;
    server_name _;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;

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
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
    }

    location /api/internal/ml/ {
        proxy_pass http://ml_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 50M;
    access_log /var/log/nginx/harvey_access.log;
    error_log /var/log/nginx/harvey_error.log;
}
EOF

ln -sf /etc/nginx/sites-available/harvey /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t

echo "✅ Nginx configured"

# ============================================
# STEP 9: Configure Firewall
# ============================================

echo "🔥 Configuring UFW firewall..."

ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

echo "✅ Firewall configured"

# ============================================
# STEP 10: Start All Services
# ============================================

echo "🚀 Starting services..."

systemctl daemon-reload
systemctl enable harvey.service nginx

if [ -f "/etc/systemd/system/ml-api.service" ]; then
    systemctl enable ml-api.service
    systemctl restart ml-api.service
fi

systemctl restart harvey.service
systemctl restart nginx

sleep 5

# ============================================
# STEP 11: Health Checks
# ============================================

echo ""
echo "🔍 Running health checks..."
echo ""

curl -s http://127.0.0.1:8000/ > /dev/null && echo "✅ Harvey backend: OK" || echo "❌ Harvey backend: FAILED"
curl -s http://127.0.0.1/ > /dev/null && echo "✅ Nginx: OK" || echo "❌ Nginx: FAILED"

if [ -f "/etc/systemd/system/ml-api.service" ]; then
    curl -s http://127.0.0.1:9000/health > /dev/null && echo "✅ ML API: OK" || echo "⚠️  ML API: Not running (expected if not deployed)"
fi

# ============================================
# DEPLOYMENT COMPLETE
# ============================================

echo ""
echo "=========================================="
echo "✅ Harvey Deployment Complete!"
echo "=========================================="
echo ""
echo "🌐 Access Harvey at: http://$(curl -s ifconfig.me)/"
echo ""
echo "📊 Service Status:"
systemctl is-active harvey.service && echo "  ✅ Harvey Backend: Running" || echo "  ❌ Harvey Backend: Failed"
systemctl is-active nginx && echo "  ✅ Nginx: Running" || echo "  ❌ Nginx: Failed"
if [ -f "/etc/systemd/system/ml-api.service" ]; then
    systemctl is-active ml-api.service && echo "  ✅ ML API: Running" || echo "  ⚠️  ML API: Not running"
fi
echo ""
echo "📝 Useful commands:"
echo "  View Harvey logs:     journalctl -u harvey.service -f"
echo "  View ML API logs:     journalctl -u ml-api.service -f"
echo "  Restart Harvey:       systemctl restart harvey.service"
echo "  Check status:         systemctl status harvey.service"
echo "  Update from GitHub:   cd /opt/harvey-backend && git pull && systemctl restart harvey.service"
echo ""
echo "🔐 Environment file: /opt/harvey-backend/.env"
echo ""
