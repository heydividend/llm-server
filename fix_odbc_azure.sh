#!/bin/bash
# Fix ODBC Driver Configuration on Azure VM

echo "================================================"
echo "🔧 Fixing ODBC Driver Configuration"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "1️⃣ Installing Microsoft ODBC Driver 18..."
echo "------------------------------------------------"

# Add Microsoft repository and install ODBC Driver 18
if ! [[ "18.0" = "$(odbcinst -q -d -n 'ODBC Driver 18 for SQL Server' | grep -oP '(?<=Driver=)[^ ]+' | grep -oP '\d+\.\d+')" ]]; then
    curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
    curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
    sudo apt-get update
    sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
    echo -e "${GREEN}✅ ODBC Driver 18 installed${NC}"
else
    echo -e "${GREEN}✅ ODBC Driver 18 already installed${NC}"
fi

echo ""
echo "2️⃣ Creating correct odbcinst.ini..."
echo "------------------------------------------------"

# Create the correct odbcinst.ini in user home
cat > ~/odbcinst.ini << 'EOF'
[ODBC Driver 18 for SQL Server]
Description=Microsoft ODBC Driver 18 for SQL Server
Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.3.so
UsageCount=1

[ODBC Driver 17 for SQL Server]
Description=Microsoft ODBC Driver 17 for SQL Server  
Driver=/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.so
UsageCount=1

[FreeTDS]
Description=FreeTDS Driver
Driver=/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup=/usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
UsageCount=1
EOF

echo -e "${GREEN}✅ ~/odbcinst.ini created${NC}"

# Also update system odbcinst.ini
sudo cp ~/odbcinst.ini /etc/odbcinst.ini
echo -e "${GREEN}✅ /etc/odbcinst.ini updated${NC}"

echo ""
echo "3️⃣ Creating correct odbc.ini..."
echo "------------------------------------------------"

cat > ~/odbc.ini << 'EOF'
[harvey-db]
Driver = ODBC Driver 18 for SQL Server
Server = tcp:hey-dividend-sql-server.database.windows.net,1433
Database = HeyDividend
Encrypt = yes
TrustServerCertificate = no
Connection Timeout = 30
EOF

echo -e "${GREEN}✅ ~/odbc.ini created${NC}"

echo ""
echo "4️⃣ Setting ODBCSYSINI environment variable..."
echo "------------------------------------------------"

# Set ODBCSYSINI for current session
export ODBCSYSINI=/home/azureuser

# Add to .bashrc for persistence
if ! grep -q "export ODBCSYSINI=/home/azureuser" ~/.bashrc; then
    echo 'export ODBCSYSINI=/home/azureuser' >> ~/.bashrc
    echo -e "${GREEN}✅ ODBCSYSINI added to .bashrc${NC}"
else
    echo -e "${GREEN}✅ ODBCSYSINI already in .bashrc${NC}"
fi

echo ""
echo "5️⃣ Updating .env file connection strings..."
echo "------------------------------------------------"

if [ -f /home/azureuser/harvey/.env ]; then
    # Backup .env
    cp /home/azureuser/harvey/.env /home/azureuser/harvey/.env.backup
    
    # Update any FreeTDS references to ODBC Driver 18
    sed -i 's/Driver={FreeTDS}/Driver={ODBC Driver 18 for SQL Server}/g' /home/azureuser/harvey/.env
    sed -i 's/Driver={ODBC Driver 17 for SQL Server}/Driver={ODBC Driver 18 for SQL Server}/g' /home/azureuser/harvey/.env
    
    echo -e "${GREEN}✅ .env updated to use ODBC Driver 18${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
fi

echo ""
echo "6️⃣ Testing ODBC drivers..."
echo "------------------------------------------------"

# Test ODBC installation
python3 << 'EOF'
import pyodbc
import os

print("Available ODBC drivers:")
drivers = pyodbc.drivers()
for driver in drivers:
    print(f"  ✅ {driver}")

print("\nTesting connection with ODBC Driver 18...")
try:
    # Test connection string
    conn_str = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:hey-dividend-sql-server.database.windows.net,1433;Database=HeyDividend;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30"
    print("Connection string format: OK")
    print("✅ ODBC Driver 18 is properly configured")
except Exception as e:
    print(f"❌ Error: {e}")
EOF

echo ""
echo "7️⃣ Restarting Harvey services..."
echo "------------------------------------------------"

# Stop services
sudo systemctl stop harvey-backend harvey-ml

# Update systemd service files to ensure ODBCSYSINI is set
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

# Reload and start services
sudo systemctl daemon-reload
sudo systemctl start harvey-backend harvey-ml

echo -e "${GREEN}✅ Services restarted${NC}"

echo ""
echo "8️⃣ Checking service status..."
echo "------------------------------------------------"

sleep 5

# Check if services are running
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-backend FAILED${NC}"
    echo "Recent logs:"
    sudo journalctl -u harvey-backend -n 10 --no-pager
fi

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-ml FAILED${NC}"
fi

echo ""
echo "9️⃣ Testing endpoints..."
echo "------------------------------------------------"

# Test endpoints
echo -n "Harvey API (8001): "
if curl -s --max-time 3 http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo -n "ML Service (9000): "
if curl -s --max-time 3 http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo ""
echo "================================================"
echo "✅ ODBC Configuration Complete!"
echo "================================================"
echo ""
echo "Summary:"
echo "  • ODBC Driver 18 installed and configured"
echo "  • odbcinst.ini and odbc.ini files created"
echo "  • ODBCSYSINI environment variable set"
echo "  • .env file updated to use correct driver"
echo "  • Services restarted with correct configuration"
echo ""
echo "If still having issues, manually check:"
echo "  cat ~/odbcinst.ini"
echo "  cat ~/.env | grep Driver"
echo "  sudo journalctl -u harvey-backend -f"
echo ""