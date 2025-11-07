#!/bin/bash

# Fix missing dependencies on Azure VM
# This will install ALL required Python packages for Harvey

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🔧 Fixing Missing Dependencies on Azure VM"
echo "=================================================="
echo ""
echo "Installing SQLAlchemy and all other required packages..."
echo "You'll be prompted for your password."
echo ""

ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_COMMANDS'
cd /home/azureuser/harvey

echo "1. Activating virtual environment..."
source venv/bin/activate

echo ""
echo "2. Installing critical missing dependencies..."
echo "============================================="

# Install SQLAlchemy and database drivers
pip install sqlalchemy==2.0.23
pip install pymssql==2.2.10  # For Azure SQL Server

# Install other critical dependencies
pip install aiohttp==3.9.1
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install pydantic==2.5.0
pip install pandas==2.1.3
pip install numpy==1.26.2
pip install python-multipart==0.0.6
pip install python-dotenv==1.0.0
pip install requests==2.31.0

# AI/ML dependencies
pip install google-generativeai==0.3.0
pip install azure-ai-documentintelligence==1.0.0b1
pip install openai==1.3.0

# Additional utilities
pip install httpx==0.25.2
pip install cachetools==5.3.2
pip install asyncio==3.4.3

echo ""
echo "3. Verifying critical imports..."
echo "================================="

python3 << 'PYTHON_CHECK'
import sys
try:
    import sqlalchemy
    print("✅ SQLAlchemy imported successfully")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed: {e}")
    sys.exit(1)

try:
    import pymssql
    print("✅ pymssql imported successfully")
except ImportError as e:
    print(f"❌ pymssql import failed: {e}")
    sys.exit(1)

try:
    import aiohttp
    print("✅ aiohttp imported successfully")
except ImportError as e:
    print(f"❌ aiohttp import failed: {e}")

try:
    import fastapi
    print("✅ FastAPI imported successfully")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")

print("\nAll critical imports successful!")
PYTHON_CHECK

echo ""
echo "4. Restarting Harvey service..."
echo "================================"
sudo systemctl restart harvey
sleep 5

# Check if service is running
if sudo systemctl is-active --quiet harvey; then
    echo "✅ Harvey service is now running!"
    
    echo ""
    echo "5. Testing endpoints..."
    echo "======================="
    
    # Test basic health
    echo -n "Harvey API health: "
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/healthz)
    if [ "$response" = "200" ]; then
        echo "✅ OK"
    else
        echo "❌ Failed (HTTP $response)"
    fi
    
    # Test ML scheduler endpoint
    echo -n "ML Scheduler health: "
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/health)
    if [ "$response" = "401" ]; then
        echo "✅ Working (requires auth)"
    elif [ "$response" = "200" ]; then
        echo "✅ Working"
    else
        echo "❌ Not found (HTTP $response)"
    fi
else
    echo "❌ Harvey service failed to start"
    echo ""
    echo "Recent error logs:"
    sudo journalctl -u harvey -n 30 --no-pager | grep -E "ERROR|Error|ImportError|ModuleNotFoundError"
fi

echo ""
echo "================================"
echo "Dependency installation complete!"
REMOTE_COMMANDS

echo ""
echo "=================================================="
echo "📊 Summary"
echo "=================================================="
echo ""
echo "Next step: Test the endpoints from your local machine:"
echo ""
echo "curl http://20.81.210.213:8001/v1/ml-schedulers/health \\"
echo "  -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key'"
echo ""
echo "If the service still fails, check full logs with:"
echo "ssh $AZURE_USER@$AZURE_VM_IP 'sudo journalctl -u harvey -n 100'"
echo ""
echo "=================================================="