#!/bin/bash
# Harvey Multi-Model Training System - Deployment via SSH
# Uses sshpass for automated deployment to Azure VM

set -e

AZURE_VM="20.81.210.213"
AZURE_USER="azureuser"
HARVEY_DIR="/home/azureuser/harvey"

echo "=========================================================================="
echo "Harvey Multi-Model Training System - Azure VM Deployment"
echo "=========================================================================="
echo ""

# Check if sshpass is available
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass not found. Installing..."
    sudo apt-get update && sudo apt-get install -y sshpass
fi

echo "📋 Prerequisites:"
echo "   1. Git changes should be committed (manual step)"
echo "   2. Azure VM SSH password required"
echo ""

# Prompt for password (or use environment variable)
if [ -z "$AZURE_SSH_PASSWORD" ]; then
    echo "Enter Azure VM SSH password:"
    read -s AZURE_SSH_PASSWORD
    export AZURE_SSH_PASSWORD
fi

echo ""
echo "🚀 Starting deployment..."
echo ""

# Step 1: Pull latest code on Azure VM
echo "📥 Step 1: Pulling latest code from git on Azure VM..."
sshpass -p "$AZURE_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    cd /home/azureuser/harvey
    echo "   → Current directory: $(pwd)"
    echo "   → Pulling latest changes..."
    git pull origin main 2>&1 || git pull origin master 2>&1 || echo "   ⚠️  Git pull failed - continuing anyway"
    echo "   ✅ Code updated"
ENDSSH
echo ""

# Step 2: Install Python dependencies
echo "🐍 Step 2: Installing/verifying Python dependencies..."
sshpass -p "$AZURE_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    cd /home/azureuser/harvey
    source venv/bin/activate
    
    # Install required packages
    pip install python-dotenv --quiet
    pip install openai --quiet
    pip install google-generativeai --quiet
    
    echo "   ✅ Dependencies verified"
ENDSSH
echo ""

# Step 3: Create training_data directory
echo "📁 Step 3: Creating training data directory..."
sshpass -p "$AZURE_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    mkdir -p /home/azureuser/harvey/training_data
    chmod 755 /home/azureuser/harvey/training_data
    echo "   ✅ Directory created"
ENDSSH
echo ""

# Step 4: Install systemd service and timer
echo "⚙️  Step 4: Installing systemd service and timer..."
sshpass -p "$AZURE_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    # Copy systemd files to system directory
    sudo cp /home/azureuser/harvey/azure_vm_setup/systemd/harvey-multi-model-training.service /etc/systemd/system/
    sudo cp /home/azureuser/harvey/azure_vm_setup/systemd/harvey-multi-model-training.timer /etc/systemd/system/
    
    # Set correct permissions
    sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.service
    sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.timer
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    echo "   ✅ Systemd files installed"
ENDSSH
echo ""

# Step 5: Enable and start timer
echo "🔄 Step 5: Enabling and starting multi-model training timer..."
sshpass -p "$AZURE_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    # Enable timer to start on boot
    sudo systemctl enable harvey-multi-model-training.timer
    
    # Start timer now
    sudo systemctl start harvey-multi-model-training.timer
    
    echo "   ✅ Timer enabled and started"
ENDSSH
echo ""

# Step 6: Verify installation
echo "🔍 Step 6: Verifying installation..."
sshpass -p "$AZURE_SSH_PASSWORD" ssh -o StrictHostKeyChecking=no ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "Timer Status:"
    echo "═══════════════════════════════════════════════════════════════════════"
    sudo systemctl status harvey-multi-model-training.timer --no-pager | head -12
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "Next Scheduled Runs:"
    echo "═══════════════════════════════════════════════════════════════════════"
    systemctl list-timers harvey-multi-model-training.timer --no-pager
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "Generator Script Location:"
    echo "═══════════════════════════════════════════════════════════════════════"
    ls -lh /home/azureuser/harvey/scripts/multi_model_training_generator.py
ENDSSH

echo ""
echo "=========================================================================="
echo "✅ Deployment Complete!"
echo "=========================================================================="
echo ""
echo "📊 Multi-Model Training System Status:"
echo "   • Generator: Installed at /home/azureuser/harvey/scripts/"
echo "   • Schedule: Sunday 5:00 AM UTC"
echo "   • Output: 800 questions/week (200 per model × 4 models)"
echo "   • Models: GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro"
echo ""
echo "🧪 To test the generator manually:"
echo "   ssh ${AZURE_USER}@${AZURE_VM}"
echo "   sudo systemctl start harvey-multi-model-training.service"
echo "   sudo journalctl -u harvey-multi-model-training.service -f"
echo ""
echo "📋 To check logs:"
echo "   ssh ${AZURE_USER}@${AZURE_VM}"
echo "   sudo journalctl -u harvey-multi-model-training.service -n 50"
echo ""
echo "🎓 Harvey will learn from 4 AI masters to eventually stand alone!"
echo ""
