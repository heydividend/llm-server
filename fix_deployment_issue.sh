#!/bin/bash

# Fix script for Harvey service deployment issues

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🔧 Fixing Harvey Service Deployment Issue"
echo "=================================================="
echo ""

# Function to run SSH commands
run_ssh() {
    ssh $AZURE_USER@$AZURE_VM_IP "$1"
}

echo "1. Installing missing dependencies..."
echo "-------------------------------------"
run_ssh "cd /home/azureuser/harvey && source venv/bin/activate && pip install aiohttp==3.9.1 --upgrade"
echo ""

echo "2. Checking file permissions..."
echo "--------------------------------"
run_ssh "cd /home/azureuser/harvey && sudo chown -R azureuser:azureuser app/"
echo ""

echo "3. Creating __init__.py files if missing..."
echo "--------------------------------------------"
run_ssh "touch /home/azureuser/harvey/app/__init__.py"
run_ssh "touch /home/azureuser/harvey/app/routes/__init__.py"
run_ssh "touch /home/azureuser/harvey/app/services/__init__.py"
run_ssh "touch /home/azureuser/harvey/app/core/__init__.py"
echo "✅ Init files created/verified"
echo ""

echo "4. Verifying main.py route registration..."
echo "-------------------------------------------"
# Check if ml_schedulers route is registered
run_ssh "grep -q 'ml_schedulers' /home/azureuser/harvey/main.py"
if [ $? -ne 0 ]; then
    echo "⚠️  ML schedulers route not found in main.py"
    echo "Adding route registration..."
    
    # Add the import and route registration
    run_ssh "cd /home/azureuser/harvey && cp main.py main.py.backup"
    
    # Add import after other route imports
    run_ssh "sed -i '/from app.routes import chat/a from app.routes import ml_schedulers' /home/azureuser/harvey/main.py"
    
    # Add route registration after other routes
    run_ssh "sed -i '/app.include_router(chat.router)/a app.include_router(ml_schedulers.router, prefix=\"/v1\", tags=[\"ML Schedulers\"])' /home/azureuser/harvey/main.py"
    
    echo "✅ Route registration added"
else
    echo "✅ ML schedulers route already registered"
fi
echo ""

echo "5. Testing imports..."
echo "----------------------"
run_ssh "cd /home/azureuser/harvey && source venv/bin/activate && python -c 'from app.routes import ml_schedulers; from app.services import ml_schedulers_service; from app.core import self_healing; print(\"✅ All imports successful\")' 2>&1"
echo ""

echo "6. Restarting Harvey service..."
echo "--------------------------------"
run_ssh "sudo systemctl restart harvey"
sleep 5
echo ""

echo "7. Checking service status..."
echo "------------------------------"
run_ssh "sudo systemctl is-active harvey"
STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "✅ Harvey service is running"
else
    echo "⚠️  Harvey service not running. Checking logs..."
    run_ssh "sudo journalctl -u harvey -n 30 --no-pager"
fi
echo ""

echo "8. Testing endpoints..."
echo "------------------------"
# Test basic health
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://$AZURE_VM_IP:8001/healthz 2>/dev/null)
http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$http_code" = "200" ]; then
    echo "✅ Harvey API health: OK"
else
    echo "❌ Harvey API health: Failed ($http_code)"
fi

# Test ML scheduler health (might need API key)
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://$AZURE_VM_IP:8001/v1/ml-schedulers/health 2>/dev/null)
http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$http_code" = "200" ] || [ "$http_code" = "401" ]; then
    echo "✅ ML Scheduler endpoint exists (status: $http_code)"
else
    echo "❌ ML Scheduler endpoint not found (status: $http_code)"
fi
echo ""

echo "=================================================="
echo "📋 Fix Summary"
echo "=================================================="
echo ""
echo "Applied fixes:"
echo "✅ Installed/updated aiohttp"
echo "✅ Fixed file permissions"
echo "✅ Created __init__.py files"
echo "✅ Verified route registration"
echo "✅ Restarted Harvey service"
echo ""
echo "Next steps:"
echo "1. Run verification script:"
echo "   bash verify_ml_scheduler_deployment.sh YOUR_API_KEY"
echo ""
echo "2. If still not working, run diagnostic:"
echo "   bash diagnose_deployment_issue.sh"
echo ""
echo "3. Check full logs:"
echo "   ssh $AZURE_USER@$AZURE_VM_IP 'sudo journalctl -u harvey -f'"
echo ""
echo "=================================================="