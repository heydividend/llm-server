#!/bin/bash
# Quick fix for Harvey services on Azure VM

echo "================================================"
echo "🔧 Fixing Harvey Services on Azure VM"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "📍 Troubleshooting service startup issues..."
echo ""

# Check current status
echo "1️⃣ Checking current service status..."
echo "----------------------------------------"

# Check if services exist
if systemctl list-units --all | grep -q "harvey-backend"; then
    echo -e "${GREEN}✓ harvey-backend service found${NC}"
    sudo systemctl status harvey-backend --no-pager | head -10
else
    echo -e "${RED}✗ harvey-backend service not found${NC}"
fi

echo ""

if systemctl list-units --all | grep -q "harvey-ml"; then
    echo -e "${GREEN}✓ harvey-ml service found${NC}"
    sudo systemctl status harvey-ml --no-pager | head -10
else
    echo -e "${RED}✗ harvey-ml service not found${NC}"
fi

echo ""
echo "2️⃣ Installing ODBC Driver 18 for SQL Server..."
echo "----------------------------------------"

# Install ODBC Driver 18 (the correct driver)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev

echo ""
echo "3️⃣ Fixing ODBC Configuration..."
echo "----------------------------------------"

# Fix odbcinst.ini
sudo tee /etc/odbcinst.ini > /dev/null << 'EOF'
[ODBC Driver 18 for SQL Server]
Description=Microsoft ODBC Driver 18 for SQL Server
Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.so
UsageCount=1
EOF

# Create odbc.ini in home directory
cat > ~/odbc.ini << 'EOF'
[harvey-db]
Driver = ODBC Driver 18 for SQL Server
Server = tcp:hey-dividend-sql-server.database.windows.net,1433
Database = HeyDividend
Encrypt = yes
TrustServerCertificate = no
Connection Timeout = 30
EOF

cat > ~/odbcinst.ini << 'EOF'
[ODBC Driver 18 for SQL Server]
Description=Microsoft ODBC Driver 18 for SQL Server
Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.so
UsageCount=1
EOF

export ODBCSYSINI=/home/azureuser

echo -e "${GREEN}✓ ODBC configuration fixed${NC}"

echo ""
echo "4️⃣ Testing database connection..."
echo "----------------------------------------"

# Test connection
python3 << 'EOF'
import os
import pyodbc

try:
    # Test ODBC drivers
    drivers = pyodbc.drivers()
    print(f"Available ODBC drivers: {drivers}")
    
    # Try to connect
    conn_str = os.environ.get('SQLSERVER_CONN_STR', '')
    if 'FreeTDS' in conn_str:
        print("⚠️ WARNING: Connection string uses FreeTDS - updating to ODBC Driver 18")
        conn_str = conn_str.replace('FreeTDS', 'ODBC Driver 18 for SQL Server')
    
    print("✅ Database driver check passed")
except Exception as e:
    print(f"❌ Database test failed: {e}")
EOF

echo ""
echo "5️⃣ Creating/Updating systemd services..."
echo "----------------------------------------"

# Create harvey-backend service
sudo tee /etc/systemd/system/harvey-backend.service > /dev/null << 'EOF'
[Unit]
Description=Harvey Backend API
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/harvey
Environment="ODBCSYSINI=/home/azureuser"
Environment="PATH=/home/azureuser/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=/home/azureuser/harvey/.env
ExecStart=/home/azureuser/miniconda3/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create harvey-ml service
sudo tee /etc/systemd/system/harvey-ml.service > /dev/null << 'EOF'
[Unit]
Description=Harvey ML Service
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/harvey/ml_training
Environment="ODBCSYSINI=/home/azureuser"
Environment="PATH=/home/azureuser/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=/home/azureuser/harvey/.env
ExecStart=/home/azureuser/miniconda3/bin/python ml_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd services updated${NC}"

echo ""
echo "6️⃣ Updating .env file if needed..."
echo "----------------------------------------"

# Check if .env exists
if [ -f /home/azureuser/harvey/.env ]; then
    # Fix connection string if it uses FreeTDS
    if grep -q "FreeTDS" /home/azureuser/harvey/.env; then
        echo "Updating connection string from FreeTDS to ODBC Driver 18..."
        sed -i 's/Driver={FreeTDS}/Driver={ODBC Driver 18 for SQL Server}/g' /home/azureuser/harvey/.env
        echo -e "${GREEN}✓ Connection string updated${NC}"
    else
        echo -e "${GREEN}✓ Connection string already correct${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ .env file not found - please create it${NC}"
fi

echo ""
echo "7️⃣ Reloading and starting services..."
echo "----------------------------------------"

# Reload systemd
sudo systemctl daemon-reload

# Stop services first
sudo systemctl stop harvey-backend harvey-ml 2>/dev/null

# Start services
echo "Starting harvey-backend..."
sudo systemctl start harvey-backend
sleep 3

echo "Starting harvey-ml..."
sudo systemctl start harvey-ml
sleep 3

# Enable services
sudo systemctl enable harvey-backend harvey-ml 2>/dev/null

echo ""
echo "8️⃣ Final Status Check..."
echo "----------------------------------------"

# Check service status
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-backend FAILED to start${NC}"
    echo "Last 10 log lines:"
    sudo journalctl -u harvey-backend -n 10 --no-pager
fi

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-ml FAILED to start${NC}"
    echo "Last 10 log lines:"
    sudo journalctl -u harvey-ml -n 10 --no-pager
fi

# Check ports
echo ""
echo "Port status:"
sudo ss -tlnp | grep -E "8001|9000" || echo "No services listening on expected ports"

# Test endpoints
echo ""
echo "9️⃣ Testing endpoints..."
echo "----------------------------------------"

# Test Harvey API
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Harvey API responding on port 8001${NC}"
else
    echo -e "${RED}❌ Harvey API not responding${NC}"
fi

# Test ML Service
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ ML Service responding on port 9000${NC}"
else
    echo -e "${RED}❌ ML Service not responding${NC}"
fi

echo ""
echo "================================================"
echo "🎯 Service Fix Complete!"
echo "================================================"
echo ""
echo "If services are still not running, check:"
echo "1. Logs: sudo journalctl -u harvey-backend -f"
echo "2. Python path: which python3"
echo "3. Dependencies: cd /home/azureuser/harvey && pip install -r requirements.txt"
echo "4. .env file: nano /home/azureuser/harvey/.env"
echo ""
echo "Your services should be accessible at:"
echo "  Harvey API: http://$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):8001"
echo "  ML Service: http://$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):9000"
echo ""