#!/bin/bash
set -e

AZURE_VM="20.81.210.213"
AZURE_USER="azureuser"

echo "🚀 Deploying Harvey Multi-Model Training System to Azure VM..."
echo ""

# Step 1: Copy generator script
echo "📤 Copying multi-model training generator..."
scp -o StrictHostKeyChecking=no scripts/multi_model_training_generator.py ${AZURE_USER}@${AZURE_VM}:/home/azureuser/harvey/scripts/ 2>&1

# Step 2: Copy systemd files
echo "📤 Copying systemd service and timer..."
scp -o StrictHostKeyChecking=no azure_vm_setup/systemd/harvey-multi-model-training.service ${AZURE_USER}@${AZURE_VM}:/tmp/ 2>&1
scp -o StrictHostKeyChecking=no azure_vm_setup/systemd/harvey-multi-model-training.timer ${AZURE_USER}@${AZURE_VM}:/tmp/ 2>&1

# Step 3: Install on Azure VM
echo "🔧 Installing systemd service..."
ssh -o StrictHostKeyChecking=no ${AZURE_USER}@${AZURE_VM} << 'ENDSSH'
    sudo cp /tmp/harvey-multi-model-training.service /etc/systemd/system/
    sudo cp /tmp/harvey-multi-model-training.timer /etc/systemd/system/
    sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.*
    mkdir -p /home/azureuser/harvey/training_data
    sudo systemctl daemon-reload
    sudo systemctl enable harvey-multi-model-training.timer
    sudo systemctl start harvey-multi-model-training.timer
    echo "✅ Service installed and enabled"
ENDSSH

# Step 4: Verify
echo ""
echo "🔍 Verifying installation..."
ssh -o StrictHostKeyChecking=no ${AZURE_USER}@${AZURE_VM} "systemctl list-timers harvey-multi-model-training.timer --no-pager"

echo ""
echo "✅ Deployment Complete!"
