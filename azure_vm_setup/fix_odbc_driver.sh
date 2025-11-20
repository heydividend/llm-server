#!/bin/bash

echo "=================================================================="
echo "Harvey AI - ODBC Driver 18 Dependency Fix"
echo "=================================================================="
echo ""

echo "📦 Step 1: Installing missing dependencies..."
sudo apt-get update
sudo apt-get install -y unixodbc unixodbc-dev libodbc1 libgssapi-krb5-2 libssl1.1

echo ""
echo "🔍 Step 2: Checking current ODBC driver status..."
if [ -f /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.3.so.2.1 ]; then
    echo "✓ ODBC Driver 18 library found"
    echo ""
    echo "Checking for missing dependencies:"
    ldd /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.3.so.2.1 | grep "not found" || echo "✓ All dependencies satisfied"
else
    echo "⚠ ODBC Driver 18 not found, will install fresh"
fi

echo ""
echo "🔄 Step 3: Reinstalling ODBC Driver 18..."
sudo ACCEPT_EULA=Y apt-get install --reinstall -y msodbcsql18

echo ""
echo "✅ Step 4: Verifying installation..."
odbcinst -q -d -n "ODBC Driver 18 for SQL Server"

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================================="
    echo "✅ ODBC Driver 18 Fixed Successfully!"
    echo "=================================================================="
    echo ""
    echo "📝 Test database connection with:"
    echo "  cd /home/azureuser/harvey"
    echo "  python3 scripts/data_scientist_agent.py --schema-only"
    echo ""
else
    echo ""
    echo "=================================================================="
    echo "❌ Installation verification failed"
    echo "=================================================================="
    echo ""
    echo "Please check the error messages above and try:"
    echo "  1. sudo apt-get update"
    echo "  2. sudo apt-get install -y msodbcsql18"
    echo ""
fi
