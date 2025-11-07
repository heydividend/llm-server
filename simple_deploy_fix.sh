#!/bin/bash

# Simple deployment fix for ML Scheduler endpoints
# This script uses simpler methods to avoid quote issues

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🔧 Simple ML Scheduler Deployment Fix"
echo "=================================================="
echo ""

# Function to execute SSH commands
ssh_exec() {
    ssh $AZURE_USER@$AZURE_VM_IP "$1"
}

echo "1. Creating backup..."
ssh_exec "cp /home/azureuser/harvey/main.py /home/azureuser/harvey/main.py.backup_$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup created"
echo ""

echo "2. Copying ML scheduler files from Replit to Azure VM..."
# First, let's copy the actual files from our local environment
scp app/routes/ml_schedulers.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/routes/ml_schedulers.py
scp app/services/ml_schedulers_service.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_schedulers_service.py
scp app/core/self_healing.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/core/self_healing.py
scp app/services/ml_api_client.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_api_client.py
scp app/services/ml_integration.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_integration.py
echo "✅ Files copied"
echo ""

echo "3. Creating Python script to update main.py..."
# Create a temporary Python script on the VM
ssh_exec 'cat > /tmp/update_main.py << '\''SCRIPT'\''
import sys

# Read main.py
with open("/home/azureuser/harvey/main.py", "r") as f:
    lines = f.readlines()

# Check if ml_schedulers import exists
has_import = False
has_router = False

for line in lines:
    if "from app.routes import ml_schedulers" in line:
        has_import = True
    if "ml_schedulers.router" in line:
        has_router = True

# Add import if missing
if not has_import:
    for i, line in enumerate(lines):
        if "from app.routes import" in line:
            # Add after the last route import
            lines.insert(i + 1, "from app.routes import ml_schedulers\n")
            print("Added ml_schedulers import")
            break

# Add router if missing
if not has_router:
    for i, line in enumerate(lines):
        if "app.include_router" in line and "chat.router" in line:
            # Add after chat router
            lines.insert(i + 1, "app.include_router(ml_schedulers.router, prefix=\"/v1\", tags=[\"ML Schedulers\"])\n")
            print("Added ml_schedulers router")
            break

# Write back
with open("/home/azureuser/harvey/main.py", "w") as f:
    f.writelines(lines)

print("main.py updated successfully")
SCRIPT'

echo "✅ Update script created"
echo ""

echo "4. Running update script..."
ssh_exec "cd /home/azureuser/harvey && python3 /tmp/update_main.py"
echo ""

echo "5. Verifying main.py changes..."
ssh_exec "grep -n ml_schedulers /home/azureuser/harvey/main.py | head -5"
echo ""

echo "6. Installing dependencies..."
ssh_exec "cd /home/azureuser/harvey && source venv/bin/activate && pip install aiohttp --upgrade --quiet"
echo "✅ Dependencies installed"
echo ""

echo "7. Restarting Harvey service..."
ssh_exec "sudo systemctl restart harvey"
echo "Waiting for service to start..."
sleep 8
echo ""

echo "8. Checking service status..."
if ssh_exec "sudo systemctl is-active --quiet harvey"; then
    echo "✅ Harvey service is running"
else
    echo "❌ Harvey service failed. Checking error..."
    ssh_exec "sudo journalctl -u harvey -n 20 --no-pager | grep -i error | head -10"
    echo ""
    echo "Trying to start manually to see error..."
    ssh_exec "cd /home/azureuser/harvey && source venv/bin/activate && timeout 3 python main.py 2>&1 | head -20"
fi
echo ""

echo "9. Testing endpoints..."
echo "------------------------"

# Test basic health first
echo -n "Harvey API health: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://$AZURE_VM_IP:8001/healthz)
if [ "$response" = "200" ]; then
    echo "✅ OK"
else
    echo "❌ Failed (HTTP $response)"
fi

# Test ML scheduler endpoint
echo -n "ML Scheduler endpoint: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://$AZURE_VM_IP:8001/v1/ml-schedulers/health)
if [ "$response" = "200" ] || [ "$response" = "401" ]; then
    echo "✅ Working (HTTP $response)"
    if [ "$response" = "401" ]; then
        echo "   Use API key for full access"
    fi
else
    echo "❌ Not found (HTTP $response)"
fi

echo ""
echo "10. Available routes on server:"
echo "--------------------------------"
curl -s http://$AZURE_VM_IP:8001/docs 2>/dev/null | grep -o '/v1/[^"]*' | sort -u | head -10

echo ""
echo "=================================================="
echo "📋 Deployment Status"
echo "=================================================="
echo ""

if [ "$response" = "200" ] || [ "$response" = "401" ]; then
    echo "✅ SUCCESS! ML Scheduler endpoints are now deployed."
    echo ""
    echo "Test with your API key:"
    echo "curl http://$AZURE_VM_IP:8001/v1/ml-schedulers/health \\"
    echo "  -H 'Authorization: Bearer YOUR_API_KEY'"
else
    echo "⚠️  Deployment may have issues. Check:"
    echo "1. Service logs: ssh $AZURE_USER@$AZURE_VM_IP 'sudo journalctl -u harvey -n 50'"
    echo "2. Import errors: ssh $AZURE_USER@$AZURE_VM_IP 'cd /home/azureuser/harvey && source venv/bin/activate && python -c \"from app.routes import ml_schedulers\"'"
    echo "3. Main.py content: ssh $AZURE_USER@$AZURE_VM_IP 'cat /home/azureuser/harvey/main.py | grep ml_schedulers'"
fi

echo ""
echo "=================================================="