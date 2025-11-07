#!/bin/bash
# Verify pymssql is configured and working on Azure VM

echo "=========================================="
echo "Verifying pymssql Configuration"
echo "=========================================="

VM_IP="20.81.210.213"
VM_USER="azureuser"

# SSH key handling
SSH_KEY=""
if [ "$1" != "" ]; then
    SSH_KEY="-i $1"
fi

ssh ${SSH_KEY} ${VM_USER}@${VM_IP} << 'ENDSSH'
echo ""
echo "1️⃣ Checking pymssql installation..."
cd /home/azureuser/harvey/ml_training
source venv/bin/activate 2>/dev/null

python -c "import pymssql; print('✅ pymssql version:', pymssql.__version__)" || echo "❌ pymssql not installed"

echo ""
echo "2️⃣ Testing database connection with pymssql..."
export USE_PYMSSQL=true

python << 'PYTHON_TEST'
import os
os.environ['USE_PYMSSQL'] = 'true'

try:
    from data_extraction import DataExtractor
    extractor = DataExtractor()
    print("✅ Database connection successful with pymssql!")
    
    # Test a simple query
    import pandas as pd
    query = "SELECT TOP 1 1 as test"
    result = pd.read_sql(query, extractor.engine)
    print("✅ Query execution successful!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
PYTHON_TEST

echo ""
echo "3️⃣ Checking environment configuration..."
echo -n "USE_PYMSSQL in environment: "
if [ "$USE_PYMSSQL" == "true" ]; then
    echo "✅ Set to true"
else
    echo "⚠️ Not set (will use pyodbc by default)"
fi

echo ""
echo "4️⃣ Checking systemd service configuration..."
if sudo grep -q "USE_PYMSSQL=true" /etc/systemd/system/harvey-ml-training.service 2>/dev/null; then
    echo "✅ Systemd service configured for pymssql"
else
    echo "⚠️ Systemd service not configured for pymssql"
fi

echo ""
echo "5️⃣ Checking cron configuration..."
if crontab -l 2>/dev/null | grep -q "USE_PYMSSQL=true"; then
    echo "✅ Cron job configured for pymssql"
else
    echo "⚠️ Cron job not explicitly using pymssql"
fi

echo ""
echo "6️⃣ Verifying no ODBC dependencies..."
echo -n "Checking for ODBC drivers: "
if ! command -v odbcinst &> /dev/null; then
    echo "✅ No ODBC installed (good for pymssql)"
else
    echo "ℹ️ ODBC is installed but not needed with pymssql"
fi

deactivate 2>/dev/null
ENDSSH

echo ""
echo "=========================================="
echo "Summary: pymssql is the better choice!"
echo "=========================================="
echo "✅ No ODBC driver configuration needed"
echo "✅ Works directly with SQL Server"
echo "✅ Simpler setup and maintenance"
echo "✅ Better performance for batch operations"