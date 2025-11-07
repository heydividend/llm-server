#!/bin/bash

# Direct SSH commands to check and fix route registration on Azure VM

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🔍 Checking Route Registration on Azure VM"
echo "=================================================="
echo ""
echo "Enter your password when prompted:"
echo ""

ssh $AZURE_USER@$AZURE_VM_IP << 'SSH_COMMANDS'
cd /home/azureuser/harvey

echo "1. Checking if ml_schedulers files exist:"
echo "=========================================="
ls -la app/routes/ml_schedulers.py 2>/dev/null && echo "✅ ml_schedulers.py exists" || echo "❌ ml_schedulers.py missing"
ls -la app/services/ml_schedulers_service.py 2>/dev/null && echo "✅ ml_schedulers_service.py exists" || echo "❌ ml_schedulers_service.py missing"

echo ""
echo "2. Checking main.py for ml_schedulers registration:"
echo "===================================================="
grep -n "ml_schedulers" main.py || echo "❌ ml_schedulers NOT found in main.py"

echo ""
echo "3. Checking if ml_schedulers.py has correct router prefix:"
echo "==========================================================="
grep "router = APIRouter" app/routes/ml_schedulers.py

echo ""
echo "4. Checking current routes registered in the app:"
echo "=================================================="
curl -s http://localhost:8001/openapi.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
paths = data.get('paths', {})
ml_routes = [p for p in paths if 'ml-scheduler' in p]
if ml_routes:
    print('✅ ML Scheduler routes found:')
    for route in ml_routes:
        print(f'   {route}')
else:
    print('❌ No ML Scheduler routes found in OpenAPI')
    print('Available routes:')
    for i, route in enumerate(list(paths.keys())[:10]):
        print(f'   {route}')
"

echo ""
echo "5. Fixing main.py registration (if needed):"
echo "============================================"

# Check if ml_schedulers import exists
if ! grep -q "from app.routes import ml_schedulers" main.py; then
    echo "Adding ml_schedulers import..."
    # Add import after chat import
    sed -i '/from app.routes import chat/a from app.routes import ml_schedulers' main.py
    echo "✅ Added import"
else
    echo "✅ Import already exists"
fi

# Check if ml_schedulers router is registered
if ! grep -q "ml_schedulers.router" main.py; then
    echo "Adding ml_schedulers router registration..."
    # Add router registration after chat router
    sed -i '/app.include_router(chat.router/a app.include_router(ml_schedulers.router, prefix="/v1", tags=["ML Schedulers"])' main.py
    echo "✅ Added router registration"
else
    echo "✅ Router registration already exists"
fi

echo ""
echo "6. Showing the relevant lines from main.py:"
echo "============================================"
echo "Imports section:"
grep -A2 -B2 "from app.routes import" main.py | head -10
echo ""
echo "Router registration section:"
grep -A2 -B2 "app.include_router" main.py | head -15

echo ""
echo "7. Restarting Harvey service..."
echo "================================"
sudo systemctl restart harvey
sleep 5

if sudo systemctl is-active --quiet harvey; then
    echo "✅ Service restarted successfully"
    
    echo ""
    echo "8. Testing endpoints after restart:"
    echo "===================================="
    
    # Test ML scheduler health
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/health)
    if [ "$response" = "401" ]; then
        echo "✅ SUCCESS! ML Scheduler health endpoint is working (401 = needs auth)"
    elif [ "$response" = "200" ]; then
        echo "✅ SUCCESS! ML Scheduler health endpoint is working (200 OK)"
    else
        echo "❌ ML Scheduler health endpoint still not found (HTTP $response)"
        
        echo ""
        echo "Checking for import errors:"
        sudo journalctl -u harvey -n 20 --no-pager | grep -i "import\|module\|error" | head -10
    fi
else
    echo "❌ Service failed to start. Recent errors:"
    sudo journalctl -u harvey -n 30 --no-pager | grep -i error
fi
SSH_COMMANDS

echo ""
echo "=================================================="
echo "📊 Diagnostic Complete"
echo "=================================================="
echo ""
echo "Now test from your local machine:"
echo "curl http://20.81.210.213:8001/v1/ml-schedulers/health \\"
echo "  -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key'"
echo ""
echo "=================================================="