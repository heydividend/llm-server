#!/bin/bash
# Complete ODBC Fix for Azure VM

echo "================================================"
echo "🔧 Complete ODBC Configuration Fix"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "1️⃣ Checking ODBC file locations..."
echo "------------------------------------------------"

echo "System ODBC files:"
ls -la /etc/odbc* 2>/dev/null || echo "  No files in /etc/"

echo ""
echo "User ODBC files:"
ls -la ~/odbc* 2>/dev/null || echo "  No files in home directory"

echo ""
echo "2️⃣ Installing Microsoft ODBC Driver 18..."
echo "------------------------------------------------"

# Install ODBC Driver 18 if not present
if ! odbcinst -q -d -n "ODBC Driver 18 for SQL Server" 2>/dev/null | grep -q Driver; then
    echo "Installing ODBC Driver 18..."
    curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
    curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
    sudo apt-get update
    sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
    echo -e "${GREEN}✅ ODBC Driver 18 installed${NC}"
else
    echo -e "${GREEN}✅ ODBC Driver 18 already installed${NC}"
fi

echo ""
echo "3️⃣ Creating odbcinst.ini in HOME directory..."
echo "------------------------------------------------"

# Create odbcinst.ini in home directory
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

echo -e "${GREEN}✅ Created ~/odbcinst.ini${NC}"
echo "Contents:"
cat ~/odbcinst.ini

echo ""
echo "4️⃣ Creating odbc.ini in HOME directory..."
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

echo -e "${GREEN}✅ Created ~/odbc.ini${NC}"

echo ""
echo "5️⃣ Setting ODBCSYSINI environment variable..."
echo "------------------------------------------------"

# Set for current session
export ODBCSYSINI=/home/azureuser

# Add to .bashrc if not there
if ! grep -q "export ODBCSYSINI=/home/azureuser" ~/.bashrc; then
    echo 'export ODBCSYSINI=/home/azureuser' >> ~/.bashrc
    echo -e "${GREEN}✅ Added ODBCSYSINI to ~/.bashrc${NC}"
fi

# Add to /etc/environment for system-wide
if ! grep -q "ODBCSYSINI=/home/azureuser" /etc/environment; then
    echo 'ODBCSYSINI=/home/azureuser' | sudo tee -a /etc/environment
    echo -e "${GREEN}✅ Added ODBCSYSINI to /etc/environment${NC}"
fi

echo ""
echo "6️⃣ Updating .env file..."
echo "------------------------------------------------"

if [ -f /home/azureuser/harvey/.env ]; then
    cd /home/azureuser/harvey
    
    # Backup .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    
    # Fix any FreeTDS or Driver 17 references
    sed -i 's/Driver={FreeTDS}/Driver={ODBC Driver 18 for SQL Server}/g' .env
    sed -i 's/Driver={ODBC Driver 17 for SQL Server}/Driver={ODBC Driver 18 for SQL Server}/g' .env
    
    echo -e "${GREEN}✅ Updated .env to use ODBC Driver 18${NC}"
    
    # Show connection string format
    echo ""
    echo "Connection string should look like:"
    echo "SQLSERVER_CONN_STR=\"Driver={ODBC Driver 18 for SQL Server};Server=tcp:hey-dividend-sql-server.database.windows.net,1433;Database=HeyDividend;UID=your_username;PWD=your_password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30\""
else
    echo -e "${RED}❌ .env file not found at /home/azureuser/harvey/.env${NC}"
fi

echo ""
echo "7️⃣ Testing ODBC configuration..."
echo "------------------------------------------------"

python3 << 'EOPY'
import pyodbc
import os

# Set ODBCSYSINI
os.environ['ODBCSYSINI'] = '/home/azureuser'

print("ODBCSYSINI set to:", os.environ.get('ODBCSYSINI'))
print("\nAvailable ODBC drivers:")

try:
    drivers = pyodbc.drivers()
    for driver in drivers:
        if 'SQL Server' in driver or 'FreeTDS' in driver:
            print(f"  ✅ {driver}")
        else:
            print(f"  • {driver}")
    
    if 'ODBC Driver 18 for SQL Server' in drivers:
        print("\n✅ ODBC Driver 18 is properly installed and configured!")
    else:
        print("\n❌ ODBC Driver 18 not found in available drivers")
        
except Exception as e:
    print(f"❌ Error checking drivers: {e}")
EOPY

echo ""
echo "8️⃣ Updating systemd services with ODBCSYSINI..."
echo "------------------------------------------------"

# Update harvey-backend service
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Updated harvey-backend.service${NC}"

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "9️⃣ Restarting Harvey services..."
echo "------------------------------------------------"

# Stop and start services
sudo systemctl stop harvey-backend harvey-ml
sleep 2
sudo systemctl start harvey-backend
sleep 3
sudo systemctl start harvey-ml

# Check status
echo ""
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-backend FAILED${NC}"
    echo "Last error logs:"
    sudo journalctl -u harvey-backend -n 10 --no-pager | grep -i error | tail -3
fi

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-ml FAILED${NC}"
fi

echo ""
echo "🔟 Testing endpoints..."
echo "------------------------------------------------"

echo -n "Harvey API (localhost:8001): "
if curl -s --max-time 3 http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo -n "ML Service (localhost:9000): "
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
echo "📍 ODBC File Locations:"
echo "  • odbcinst.ini: ~/odbcinst.ini"
echo "  • odbc.ini: ~/odbc.ini"
echo "  • ODBCSYSINI: /home/azureuser"
echo ""
echo "If still having issues:"
echo "  1. Check: echo \$ODBCSYSINI"
echo "  2. Check: ls -la ~/odbc*.ini"
echo "  3. Check: sudo journalctl -u harvey-backend -f"
echo "  4. Test: python3 -c \"import pyodbc; print(pyodbc.drivers())\""
echo ""