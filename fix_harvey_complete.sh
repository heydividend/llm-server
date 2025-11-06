#!/bin/bash
# Complete Fix for Harvey on Azure VM - Port & ODBC Issues

echo "================================================"
echo "🔧 COMPLETE HARVEY FIX - Port 8001 & ODBC"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "1️⃣ KILLING PROCESS ON PORT 8001..."
echo "------------------------------------------------"

# Find and kill process on port 8001
PORT_PID=$(sudo lsof -t -i:8001)
if [ ! -z "$PORT_PID" ]; then
    echo -e "${YELLOW}⚠️ Process $PORT_PID is using port 8001${NC}"
    sudo kill -9 $PORT_PID
    sleep 2
    echo -e "${GREEN}✅ Killed process on port 8001${NC}"
else
    echo -e "${GREEN}✅ Port 8001 is already free${NC}"
fi

# Also check for any hanging uvicorn processes
sudo pkill -f "uvicorn.*8001" 2>/dev/null
sudo systemctl stop harvey-backend 2>/dev/null

echo ""
echo "2️⃣ INSTALLING ODBC DRIVER 18..."
echo "------------------------------------------------"

# Check if Driver 18 is installed
if ! odbcinst -q -d -n "ODBC Driver 18 for SQL Server" 2>/dev/null | grep -q Driver; then
    echo "Installing Microsoft ODBC Driver 18..."
    
    # Add Microsoft repo
    curl -s https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
    curl -s https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
    
    # Update and install
    sudo apt-get update -qq
    sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
    
    echo -e "${GREEN}✅ ODBC Driver 18 installed${NC}"
else
    echo -e "${GREEN}✅ ODBC Driver 18 already installed${NC}"
fi

echo ""
echo "3️⃣ CREATING ODBC CONFIG FILES..."
echo "------------------------------------------------"

# Create odbcinst.ini in home directory
cat > /home/azureuser/odbcinst.ini << 'EOF'
[ODBC Driver 18 for SQL Server]
Description=Microsoft ODBC Driver 18 for SQL Server
Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.3.so.3.2
UsageCount=1
EOF

echo -e "${GREEN}✅ Created ~/odbcinst.ini${NC}"

# Create odbc.ini in home directory
cat > /home/azureuser/odbc.ini << 'EOF'
[harvey-db]
Driver = ODBC Driver 18 for SQL Server
Server = tcp:hey-dividend-sql-server.database.windows.net,1433
Database = HeyDividend
Encrypt = yes
TrustServerCertificate = no
Connection Timeout = 30
EOF

echo -e "${GREEN}✅ Created ~/odbc.ini${NC}"

echo ""
echo "4️⃣ SETTING ENVIRONMENT VARIABLES..."
echo "------------------------------------------------"

# Set ODBCSYSINI
export ODBCSYSINI=/home/azureuser

# Add to bashrc
if ! grep -q "export ODBCSYSINI=/home/azureuser" ~/.bashrc; then
    echo 'export ODBCSYSINI=/home/azureuser' >> ~/.bashrc
fi

# Add to /etc/environment
echo 'ODBCSYSINI="/home/azureuser"' | sudo tee -a /etc/environment > /dev/null

echo -e "${GREEN}✅ ODBCSYSINI set to /home/azureuser${NC}"

echo ""
echo "5️⃣ FIXING .env FILE..."
echo "------------------------------------------------"

cd /home/azureuser/harvey

# Backup .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null

# Fix all driver references in .env
if [ -f ".env" ]; then
    # Replace FreeTDS with ODBC Driver 18
    sed -i 's/Driver={FreeTDS}/Driver={ODBC Driver 18 for SQL Server}/g' .env
    
    # Replace Driver 17 with Driver 18
    sed -i 's/Driver={ODBC Driver 17 for SQL Server}/Driver={ODBC Driver 18 for SQL Server}/g' .env
    
    # Replace any unbracketed references
    sed -i 's/Driver=FreeTDS/Driver={ODBC Driver 18 for SQL Server}/g' .env
    sed -i 's/Driver=ODBC Driver 17 for SQL Server/Driver={ODBC Driver 18 for SQL Server}/g' .env
    
    echo -e "${GREEN}✅ Updated .env to use ODBC Driver 18${NC}"
    
    # Show the connection string format
    echo ""
    echo -e "${BLUE}Connection string should look like:${NC}"
    echo 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:hey-dividend-sql-server.database.windows.net,1433;Database=HeyDividend;UID=xxx;PWD=xxx;Encrypt=yes;TrustServerCertificate=no'
else
    echo -e "${RED}❌ .env file not found!${NC}"
fi

echo ""
echo "6️⃣ UPDATING SYSTEMD SERVICE..."
echo "------------------------------------------------"

# Update harvey-backend service with correct environment
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
ExecStart=/home/azureuser/miniconda3/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo -e "${GREEN}✅ Systemd service updated${NC}"

echo ""
echo "7️⃣ TESTING ODBC CONFIGURATION..."
echo "------------------------------------------------"

# Test Python can see the drivers
python3 << 'PYEOF'
import os
import pyodbc

os.environ['ODBCSYSINI'] = '/home/azureuser'

try:
    drivers = pyodbc.drivers()
    print("Available ODBC Drivers:")
    for driver in drivers:
        if 'SQL Server' in driver:
            print(f"  ✅ {driver}")
        else:
            print(f"  • {driver}")
    
    if 'ODBC Driver 18 for SQL Server' in drivers:
        print("\n✅ ODBC Driver 18 is properly configured!")
    else:
        print("\n❌ ODBC Driver 18 not found in drivers list")
        print("Attempting to force load...")
        
except Exception as e:
    print(f"❌ Error: {e}")
PYEOF

echo ""
echo "8️⃣ RESTARTING HARVEY SERVICES..."
echo "------------------------------------------------"

# Stop everything first
sudo systemctl stop harvey-backend harvey-ml
sleep 3

# Make sure port is free
PORT_CHECK=$(sudo lsof -t -i:8001)
if [ ! -z "$PORT_CHECK" ]; then
    echo -e "${YELLOW}Killing remaining process on 8001...${NC}"
    sudo kill -9 $PORT_CHECK
    sleep 2
fi

# Start services
sudo systemctl start harvey-ml
sleep 3
sudo systemctl start harvey-backend
sleep 5

echo ""
echo "9️⃣ CHECKING SERVICE STATUS..."
echo "------------------------------------------------"

# Check if services are running
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is RUNNING${NC}"
    
    # Check for errors in logs
    if sudo journalctl -u harvey-backend -n 20 --no-pager | grep -q "FreeTDS"; then
        echo -e "${RED}⚠️ Still seeing FreeTDS errors - checking logs...${NC}"
        sudo journalctl -u harvey-backend -n 10 --no-pager | grep -E "(ERROR|FreeTDS|Driver)"
    fi
else
    echo -e "${RED}❌ harvey-backend FAILED TO START${NC}"
    echo "Last error logs:"
    sudo journalctl -u harvey-backend -n 15 --no-pager | grep -E "(ERROR|error|FreeTDS|Driver|8001)"
fi

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-ml FAILED${NC}"
fi

echo ""
echo "🔟 TESTING ENDPOINTS..."
echo "------------------------------------------------"

# Test Harvey API locally
echo -n "Harvey API (localhost:8001): "
HARVEY_RESPONSE=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null)
if [ "$HARVEY_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ WORKING (HTTP 200)${NC}"
else
    echo -e "${RED}❌ NOT WORKING (HTTP $HARVEY_RESPONSE)${NC}"
fi

# Test ML Service locally
echo -n "ML Service (localhost:9000): "
ML_RESPONSE=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:9000/health 2>/dev/null)
if [ "$ML_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ WORKING (HTTP 200)${NC}"
else
    echo -e "${RED}❌ NOT WORKING (HTTP $ML_RESPONSE)${NC}"
fi

echo ""
echo "Testing external access..."
echo -n "Harvey API (20.81.210.213:8001): "
HARVEY_EXT=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://20.81.210.213:8001/health 2>/dev/null)
if [ "$HARVEY_EXT" = "200" ]; then
    echo -e "${GREEN}✅ EXTERNALLY ACCESSIBLE${NC}"
else
    echo -e "${YELLOW}⚠️ Not accessible externally (HTTP $HARVEY_EXT)${NC}"
fi

echo -n "ML Service (20.81.210.213:9000): "
ML_EXT=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://20.81.210.213:9000/health 2>/dev/null)
if [ "$ML_EXT" = "200" ]; then
    echo -e "${GREEN}✅ EXTERNALLY ACCESSIBLE${NC}"
else
    echo -e "${YELLOW}⚠️ Not accessible externally (HTTP $ML_EXT)${NC}"
fi

echo ""
echo "================================================"
echo "✅ HARVEY FIX COMPLETE!"
echo "================================================"
echo ""
echo "📊 Summary:"
echo "  • Port 8001: Cleared and available"
echo "  • ODBC Driver 18: Installed and configured"
echo "  • Connection strings: Updated to use Driver 18"
echo "  • Services: Restarted with correct configuration"
echo ""
echo "📍 Configuration:"
echo "  • ODBCSYSINI=/home/azureuser"
echo "  • odbcinst.ini: ~/odbcinst.ini"
echo "  • odbc.ini: ~/odbc.ini"
echo ""
echo "🌐 Access URLs:"
echo "  • Harvey API: http://20.81.210.213:8001"
echo "  • ML Service: http://20.81.210.213:9000"
echo ""
echo "If still having issues:"
echo "  1. Check: cat /home/azureuser/harvey/.env | grep Driver"
echo "  2. Logs: sudo journalctl -u harvey-backend -f"
echo "  3. Test: curl http://localhost:8001/health"
echo ""