#!/bin/bash
# Harvey Multi-Model Training - Azure VM Deployment Only
# Run this AFTER committing via Replit UI

set -e

VM_USER="$AZURE_VM_USER"
VM_IP="$AZURE_VM_IP"

echo "=========================================================================="
echo "🚀 Harvey Multi-Model Training - Azure VM Deployment"
echo "=========================================================================="
echo "Target: ${VM_USER}@${VM_IP}"
echo ""

# Deploy to Azure VM
echo "📥 Step 1: Pulling latest code on Azure VM..."
ssh ${VM_USER}@${VM_IP} "cd /home/azureuser/harvey && git pull"

echo ""
echo "🔧 Step 2: Installing systemd service..."
ssh ${VM_USER}@${VM_IP} << 'INSTALL'
    cd /home/azureuser/harvey
    
    # Install systemd files
    sudo cp azure_vm_setup/systemd/harvey-multi-model-training.service /etc/systemd/system/
    sudo cp azure_vm_setup/systemd/harvey-multi-model-training.timer /etc/systemd/system/
    sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.*
    
    # Create directory
    mkdir -p training_data
    
    # Reload and enable
    sudo systemctl daemon-reload
    sudo systemctl enable harvey-multi-model-training.timer
    sudo systemctl start harvey-multi-model-training.timer
    
    echo "✅ Installation complete"
INSTALL

echo ""
echo "🔍 Step 3: Verifying deployment..."
ssh ${VM_USER}@${VM_IP} << 'VERIFY'
    echo ""
    echo "══════════════════════════════════════════════════════════════════"
    echo "Next Scheduled Run:"
    echo "══════════════════════════════════════════════════════════════════"
    systemctl list-timers harvey-multi-model-training.timer --no-pager
    
    echo ""
    echo "══════════════════════════════════════════════════════════════════"
    echo "Generator Script:"
    echo "══════════════════════════════════════════════════════════════════"
    ls -lh /home/azureuser/harvey/scripts/multi_model_training_generator.py 2>/dev/null || echo "❌ Script not found - check git pull"
    
    echo ""
    echo "══════════════════════════════════════════════════════════════════"
    echo "Service Status:"
    echo "══════════════════════════════════════════════════════════════════"
    systemctl status harvey-multi-model-training.timer --no-pager | head -8
VERIFY

echo ""
echo "=========================================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================================================="
echo ""
echo "📊 Multi-Model Training System:"
echo "   • Schedule: Sunday 5:00 AM UTC"
echo "   • Output: 800 questions/week from 4 AI models"
echo "   • Models: GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro"
echo ""
echo "🧪 Test manually:"
echo "   ssh ${VM_USER}@${VM_IP}"
echo "   sudo systemctl start harvey-multi-model-training.service"
echo "   sudo journalctl -u harvey-multi-model-training.service -f"
echo ""
echo "🎓 Harvey learns from 4 AI masters to stand alone!"
echo "=========================================================================="
