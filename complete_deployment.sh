#!/bin/bash

# Complete deployment: Fix dependencies AND deploy routes
# This combines everything in the correct order

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🚀 Complete ML Scheduler Deployment & Fix"
echo "=================================================="
echo ""
echo "This script will:"
echo "1. Install missing dependencies (SQLAlchemy, etc.)"
echo "2. Deploy the fixed ML scheduler routes"
echo "3. Restart the service and test everything"
echo ""
echo "You'll be prompted for your password several times."
echo ""
read -p "Press Enter to continue..."

# Part 1: Copy files first
echo ""
echo "📤 Step 1: Copying fixed files to Azure VM..."
echo "============================================="
scp app/routes/ml_schedulers.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/routes/ml_schedulers.py
scp app/services/ml_schedulers_service.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_schedulers_service.py
scp app/services/ml_api_client.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_api_client.py
scp app/services/ml_integration.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_integration.py
scp app/core/self_healing.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/core/self_healing.py
scp main.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/main.py

echo "✅ Files copied"

# Part 2: Install dependencies and restart
echo ""
echo "🔧 Step 2: Installing dependencies and starting service..."
echo "=========================================================="
echo "(Enter password one more time)"

ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_COMMANDS'
cd /home/azureuser/harvey
source venv/bin/activate

echo "Installing missing Python packages..."
echo "-------------------------------------"

# Core dependencies
pip install --quiet sqlalchemy==2.0.23
pip install --quiet pymssql==2.2.10
pip install --quiet aiohttp==3.9.1
pip install --quiet fastapi==0.104.1
pip install --quiet uvicorn==0.24.0
pip install --quiet pydantic==2.5.0
pip install --quiet pandas==2.1.3
pip install --quiet numpy==1.26.2
pip install --quiet python-multipart==0.0.6
pip install --quiet python-dotenv==1.0.0
pip install --quiet requests==2.31.0
pip install --quiet google-generativeai==0.3.0
pip install --quiet azure-ai-documentintelligence==1.0.0b1
pip install --quiet openai==1.3.0
pip install --quiet httpx==0.25.2
pip install --quiet cachetools==5.3.2

echo "✅ Dependencies installed"

echo ""
echo "Restarting Harvey service..."
echo "-----------------------------"
sudo systemctl restart harvey
sleep 8

# Check if service is running
if sudo systemctl is-active --quiet harvey; then
    echo "✅ Harvey service is running!"
    
    echo ""
    echo "Testing ML Scheduler Endpoints"
    echo "==============================="
    
    # Test each endpoint
    echo -n "1. Harvey API health: "
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/healthz)
    [ "$response" = "200" ] && echo "✅ OK" || echo "❌ Failed (HTTP $response)"
    
    echo -n "2. ML Scheduler health: "
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/health)
    [ "$response" = "401" ] && echo "✅ Working (auth required)" || echo "Status: $response"
    
    echo -n "3. Payout ratings: "
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/v1/ml-schedulers/payout-ratings)
    [ "$response" = "401" ] && echo "✅ Working (auth required)" || echo "Status: $response"
    
    echo -n "4. Dividend calendar: "
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/v1/ml-schedulers/dividend-calendar)
    [ "$response" = "401" ] && echo "✅ Working (auth required)" || echo "Status: $response"
    
    echo -n "5. Training status: "
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/training-status)
    [ "$response" = "401" ] && echo "✅ Working (auth required)" || echo "Status: $response"
    
    echo -n "6. Admin dashboard: "
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/admin/dashboard)
    [ "$response" = "401" ] && echo "✅ Working (auth required)" || echo "Status: $response"
    
    echo "==============================="
else
    echo "❌ Harvey service failed to start!"
    echo "Error details:"
    sudo journalctl -u harvey -n 20 --no-pager | grep -E "ERROR|Error|ImportError"
fi
REMOTE_COMMANDS

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "Test with your API key:"
echo ""
echo "curl http://20.81.210.213:8001/v1/ml-schedulers/health \\"
echo "  -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key'"
echo ""
echo "For detailed response:"
echo "curl http://20.81.210.213:8001/v1/ml-schedulers/health \\"
echo "  -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key' | python -m json.tool"
echo ""
echo "=================================================="