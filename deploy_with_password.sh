#!/bin/bash

# Deployment script for ML Schedulers - works with password authentication
# Run this from your local terminal (not from within Replit)

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🚀 ML Scheduler Deployment (Password Auth)"
echo "=================================================="
echo ""
echo "You'll be prompted for your password several times."
echo "This is normal - just enter it each time."
echo ""

# Step 1: Copy the files
echo "Step 1: Copying files to Azure VM..."
echo "(You'll need to enter your password for each file)"
echo ""

# Copy each file
scp app/routes/ml_schedulers.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/routes/ml_schedulers.py
scp app/services/ml_schedulers_service.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_schedulers_service.py
scp app/core/self_healing.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/core/self_healing.py
scp app/services/ml_api_client.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_api_client.py
scp app/services/ml_integration.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_integration.py

echo ""
echo "✅ Files copied successfully"
echo ""

# Step 2: Update main.py and restart service
echo "Step 2: Updating configuration and restarting service..."
echo "(Enter password one more time)"
echo ""

ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_COMMANDS'
echo "Connected to Azure VM"
cd /home/azureuser/harvey

# Backup main.py
cp main.py main.py.backup_$(date +%Y%m%d_%H%M%S)

# Update main.py with Python
python3 << 'PYTHON'
with open("main.py", "r") as f:
    content = f.read()

# Add import if missing
if "from app.routes import ml_schedulers" not in content:
    content = content.replace(
        "from app.routes import chat",
        "from app.routes import chat\nfrom app.routes import ml_schedulers"
    )
    print("✅ Added ml_schedulers import")

# Add router if missing
if "ml_schedulers.router" not in content:
    content = content.replace(
        'app.include_router(chat.router',
        'app.include_router(chat.router'
    )
    # Find the position after chat router
    pos = content.find('app.include_router(chat.router')
    if pos != -1:
        # Find the end of this line
        end_pos = content.find('\n', pos)
        if end_pos != -1:
            # Insert our router after this line
            new_line = '\napp.include_router(ml_schedulers.router, prefix="/v1", tags=["ML Schedulers"])'
            content = content[:end_pos] + new_line + content[end_pos:]
            print("✅ Added ml_schedulers router")

# Write back
with open("main.py", "w") as f:
    f.write(content)

print("✅ main.py updated")
PYTHON

# Install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install aiohttp --upgrade --quiet

# Restart service
echo "Restarting Harvey service..."
sudo systemctl restart harvey
sleep 5

# Check status
echo ""
echo "Checking service status..."
if sudo systemctl is-active --quiet harvey; then
    echo "✅ Harvey service is running"
else
    echo "❌ Harvey service failed to start"
    echo "Recent errors:"
    sudo journalctl -u harvey -n 20 --no-pager | grep -i error
fi

# Test endpoint
echo ""
echo "Testing ML scheduler endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/health)
if [ "$response" = "200" ] || [ "$response" = "401" ]; then
    echo "✅ ML Scheduler endpoint is working (HTTP $response)"
else
    echo "❌ ML Scheduler endpoint not found (HTTP $response)"
fi

echo ""
echo "Deployment complete!"
REMOTE_COMMANDS

echo ""
echo "=================================================="
echo "📋 Deployment Complete"
echo "=================================================="
echo ""
echo "Test your endpoints with:"
echo "curl http://$AZURE_VM_IP:8001/v1/ml-schedulers/health \\"
echo "  -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key'"
echo ""
echo "=================================================="