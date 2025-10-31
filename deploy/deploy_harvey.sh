#!/bin/bash
# Harvey Backend - Automated Deployment Script
# Run this script in /opt/harvey-backend after copying code

set -e  # Exit on error

echo "========================================="
echo "Harvey Backend - Deployment"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Are you in /opt/harvey-backend?"
    exit 1
fi

echo "📍 Current directory: $(pwd)"
echo ""

echo "🐍 Step 1: Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

echo "✅ Virtual environment created"
echo ""

echo "📦 Step 2: Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "✅ Python dependencies installed"
echo ""

echo "🔐 Step 3: Checking .env file..."
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env file with your secrets before continuing."
    echo "Example .env file has been created at .env.example"
    
    cat > .env.example <<'EOF'
# Harvey API Configuration
HARVEY_AI_API_KEY=your_harvey_api_key_here

# Azure SQL Database
SQLSERVER_HOST=your_sqlserver_host
SQLSERVER_DB=your_database_name
SQLSERVER_USER=your_username
SQLSERVER_PASSWORD=your_password

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# ML API Configuration (localhost on same VM)
ML_API_BASE_URL=http://127.0.0.1:9000/api/internal/ml
INTERNAL_ML_API_KEY=your_internal_ml_api_key

# ODBC Configuration
ODBCSYSINI=/etc

# Environment
ENVIRONMENT=production
EOF
    
    echo ""
    echo "Please edit .env file and run this script again."
    exit 1
fi

# Secure the .env file
chmod 600 .env
echo "✅ .env file secured (chmod 600)"
echo ""

echo "🔍 Step 4: Testing database connection..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

import pyodbc

conn_str = (
    f\"DRIVER={{FreeTDS}};\"
    f\"SERVER={os.getenv('SQLSERVER_HOST')};\"
    f\"DATABASE={os.getenv('SQLSERVER_DB')};\"
    f\"UID={os.getenv('SQLSERVER_USER')};\"
    f\"PWD={os.getenv('SQLSERVER_PASSWORD')};\"
    f\"TDS_Version=7.4;\"
    f\"Port=1433;\"
)

try:
    conn = pyodbc.connect(conn_str, timeout=10)
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

echo ""

echo "🔧 Step 5: Creating systemd service for Harvey..."
sudo tee /etc/systemd/system/harvey.service > /dev/null <<EOF
[Unit]
Description=Harvey AI Financial Advisor Backend
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
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

echo "✅ Harvey systemd service created"
echo ""

echo "🔧 Step 6: Creating systemd service for ML API..."
sudo tee /etc/systemd/system/ml-api.service > /dev/null <<EOF
[Unit]
Description=Harvey ML Prediction API
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/home/$USER/ml-api
Environment="PATH=/home/$USER/ml-api/venv/bin"
ExecStart=/home/$USER/ml-api/venv/bin/uvicorn main:app --host 127.0.0.1 --port 9000 --workers 2
Restart=always
RestartSec=10
StandardOutput=append:/var/log/ml-api/access.log
StandardError=append:/var/log/ml-api/error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ ML API systemd service created"
echo ""

echo "🌐 Step 7: Configuring Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/harvey > /dev/null <<'EOF'
upstream harvey_backend {
    server 127.0.0.1:8000;
}

upstream ml_api {
    server 127.0.0.1:9000;
}

server {
    listen 80;
    server_name _;

    # Increase timeouts for ML API
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;

    # Harvey Backend API
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
        
        # CORS headers
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

    # Increase client body size for file uploads
    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/harvey_access.log;
    error_log /var/log/nginx/harvey_error.log;
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/harvey /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

echo "✅ Nginx configured"
echo ""

echo "🚀 Step 8: Starting all services..."

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable harvey.service
sudo systemctl enable ml-api.service

# Start services
sudo systemctl restart harvey.service
sudo systemctl restart ml-api.service
sudo systemctl restart nginx

echo "✅ All services started"
echo ""

echo "⏳ Waiting 5 seconds for services to start..."
sleep 5

echo "🔍 Step 9: Checking service status..."
echo ""
echo "--- Harvey Backend Status ---"
sudo systemctl status harvey.service --no-pager -l
echo ""
echo "--- ML API Status ---"
sudo systemctl status ml-api.service --no-pager -l
echo ""
echo "--- Nginx Status ---"
sudo systemctl status nginx.service --no-pager -l
echo ""

echo "🧪 Step 10: Running health checks..."
echo ""

# Test Harvey backend
echo -n "Testing Harvey backend (localhost:8000)... "
if curl -s http://127.0.0.1:8000/ > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test ML API
echo -n "Testing ML API (localhost:9000)... "
if curl -s http://127.0.0.1:9000/health > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test via Nginx
echo -n "Testing via Nginx (port 80)... "
if curl -s http://127.0.0.1/ > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

echo ""
echo "========================================="
echo "🎉 Deployment Complete!"
echo "========================================="
echo ""
echo "Harvey is now running on:"
echo "  - Internal: http://127.0.0.1:8000"
echo "  - Public:   http://$(curl -s ifconfig.me)"
echo ""
echo "ML API is running on:"
echo "  - Internal: http://127.0.0.1:9000"
echo ""
echo "Useful commands:"
echo "  - View Harvey logs:  sudo journalctl -u harvey.service -f"
echo "  - View ML API logs:  sudo journalctl -u ml-api.service -f"
echo "  - View Nginx logs:   sudo tail -f /var/log/nginx/harvey_error.log"
echo "  - Restart Harvey:    sudo systemctl restart harvey.service"
echo "  - Restart ML API:    sudo systemctl restart ml-api.service"
echo ""
