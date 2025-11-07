#!/bin/bash

# Diagnostic script to find why Harvey service failed after deployment

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🔍 Diagnosing Harvey Service Deployment Issue"
echo "=================================================="
echo ""

# Function to run SSH commands
run_ssh() {
    ssh $AZURE_USER@$AZURE_VM_IP "$1"
}

# 1. Check service status
echo "1. Checking Harvey service status..."
echo "-----------------------------------"
run_ssh "sudo systemctl status harvey | head -n 20"
echo ""

# 2. Check recent error logs
echo "2. Recent error logs (last 50 lines)..."
echo "----------------------------------------"
run_ssh "sudo journalctl -u harvey -n 50 --no-pager | grep -E 'ERROR|FATAL|Failed|Error|error|ImportError|ModuleNotFoundError'"
echo ""

# 3. Check if aiohttp is installed
echo "3. Checking Python dependencies..."
echo "-----------------------------------"
run_ssh "cd /home/azureuser/harvey && source venv/bin/activate && pip list | grep -E 'aiohttp|fastapi|uvicorn'"
echo ""

# 4. Check if new files exist
echo "4. Verifying new files were synced..."
echo "--------------------------------------"
run_ssh "ls -la /home/azureuser/harvey/app/routes/ml_schedulers.py 2>/dev/null && echo '✅ ml_schedulers.py exists' || echo '❌ ml_schedulers.py missing'"
run_ssh "ls -la /home/azureuser/harvey/app/services/ml_schedulers_service.py 2>/dev/null && echo '✅ ml_schedulers_service.py exists' || echo '❌ ml_schedulers_service.py missing'"
run_ssh "ls -la /home/azureuser/harvey/app/core/self_healing.py 2>/dev/null && echo '✅ self_healing.py exists' || echo '❌ self_healing.py missing'"
echo ""

# 5. Try to import the modules manually
echo "5. Testing Python imports..."
echo "-----------------------------"
run_ssh "cd /home/azureuser/harvey && source venv/bin/activate && python -c 'import aiohttp; print(\"✅ aiohttp imports OK\")' 2>&1"
run_ssh "cd /home/azureuser/harvey && source venv/bin/activate && python -c 'from app.routes import ml_schedulers; print(\"✅ ml_schedulers routes import OK\")' 2>&1"
echo ""

# 6. Check main.py for route registration
echo "6. Checking if routes are registered in main.py..."
echo "---------------------------------------------------"
run_ssh "grep -n 'ml_schedulers' /home/azureuser/harvey/main.py | head -5"
echo ""

# 7. Try to start the app manually to see specific error
echo "7. Attempting manual start (5 second test)..."
echo "----------------------------------------------"
run_ssh "cd /home/azureuser/harvey && source venv/bin/activate && timeout 5 python main.py 2>&1 | head -20"
echo ""

# 8. Provide diagnosis
echo "=================================================="
echo "📋 Diagnosis Summary"
echo "=================================================="
echo ""
echo "Check the output above for:"
echo "1. Service status - Is it 'active' or 'failed'?"
echo "2. Error logs - Look for ImportError or ModuleNotFoundError"
echo "3. Dependencies - Is aiohttp installed?"
echo "4. Files - Are all new files present?"
echo "5. Imports - Do they work?"
echo "6. Route registration - Is ml_schedulers included?"
echo "7. Manual start - What's the specific error?"
echo ""
echo "Common fixes:"
echo "• Missing dependency: pip install aiohttp"
echo "• Import error: Check file paths and __init__.py files"
echo "• Route not registered: Update main.py"
echo "• Permission issue: Check file ownership"
echo ""
echo "=================================================="