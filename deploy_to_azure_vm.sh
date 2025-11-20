#!/bin/bash
# Harvey Multi-Model Training System - Azure VM Deployment Script
# Target: 20.81.210.213

set -e  # Exit on error

AZURE_VM="20.81.210.213"
AZURE_USER="azureuser"
HARVEY_DIR="/home/azureuser/harvey"

echo "=========================================================================="
echo "Harvey Multi-Model Training System - Azure VM Deployment"
echo "=========================================================================="
echo ""

# Step 1: Copy training generator script
echo "📤 Step 1: Copying multi-model training generator..."
scp scripts/multi_model_training_generator.py ${AZURE_USER}@${AZURE_VM}:${HARVEY_DIR}/scripts/
echo "   ✅ Generator script copied"
echo ""

# Step 2: Copy systemd files
echo "📤 Step 2: Copying systemd service and timer..."
scp azure_vm_setup/systemd/harvey-multi-model-training.service ${AZURE_USER}@${AZURE_VM}:/tmp/
scp azure_vm_setup/systemd/harvey-multi-model-training.timer ${AZURE_USER}@${AZURE_VM}:/tmp/
echo "   ✅ Systemd files copied"
echo ""

# Step 3: Install and configure on Azure VM
echo "🔧 Step 3: Installing systemd service on Azure VM..."
ssh ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    set -e
    
    # Move systemd files to correct location
    echo "   → Installing systemd service files..."
    sudo cp /tmp/harvey-multi-model-training.service /etc/systemd/system/
    sudo cp /tmp/harvey-multi-model-training.timer /etc/systemd/system/
    sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.service
    sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.timer
    
    # Create training_data directory if it doesn't exist
    mkdir -p /home/azureuser/harvey/training_data
    
    # Reload systemd
    echo "   → Reloading systemd daemon..."
    sudo systemctl daemon-reload
    
    # Enable timer
    echo "   → Enabling multi-model training timer..."
    sudo systemctl enable harvey-multi-model-training.timer
    
    # Start timer
    echo "   → Starting timer..."
    sudo systemctl start harvey-multi-model-training.timer
    
    echo "   ✅ Systemd service installed and enabled"
ENDSSH
echo ""

# Step 4: Verify installation
echo "🔍 Step 4: Verifying installation..."
ssh ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    echo ""
    echo "Timer Status:"
    sudo systemctl status harvey-multi-model-training.timer --no-pager | head -10
    echo ""
    echo "Next Scheduled Run:"
    systemctl list-timers harvey-multi-model-training.timer --no-pager
ENDSSH
echo ""

# Step 5: Test run (optional)
echo "=========================================================================="
echo "Deployment Complete! 🎉"
echo "=========================================================================="
echo ""
echo "Next scheduled run: Sunday at 5:00 AM UTC"
echo ""
echo "To manually test the generator now, run:"
echo "  ssh ${AZURE_USER}@${AZURE_VM}"
echo "  sudo systemctl start harvey-multi-model-training.service"
echo "  sudo journalctl -u harvey-multi-model-training.service -f"
echo ""
echo "To check logs:"
echo "  ssh ${AZURE_USER}@${AZURE_VM}"
echo "  sudo journalctl -u harvey-multi-model-training.service -n 50"
echo ""
