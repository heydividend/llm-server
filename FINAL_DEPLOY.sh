#!/bin/bash
# Harvey Multi-Model Training - One-Command Deployment
# Run this from your local machine where Azure SSH keys are configured

set -e

VM="20.81.210.213"
USER="azureuser"

echo "=========================================================================="
echo "Harvey Multi-Model Training System - Deployment"
echo "=========================================================================="
echo ""

echo "🔍 Step 1: Testing SSH connection..."
ssh ${USER}@${VM} "echo '✅ SSH connection successful'" || {
    echo "❌ SSH connection failed. Make sure you have SSH keys configured."
    exit 1
}

echo ""
echo "📥 Step 2: Pulling latest code from git..."
ssh ${USER}@${VM} "cd /home/azureuser/harvey && git pull"

echo ""
echo "🔧 Step 3: Installing systemd service..."
ssh ${USER}@${VM} << 'ENDSSH'
    cd /home/azureuser/harvey
    
    # Install systemd files
    sudo cp azure_vm_setup/systemd/harvey-multi-model-training.service /etc/systemd/system/
    sudo cp azure_vm_setup/systemd/harvey-multi-model-training.timer /etc/systemd/system/
    sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.*
    
    # Create directories
    mkdir -p training_data
    
    # Reload and enable
    sudo systemctl daemon-reload
    sudo systemctl enable harvey-multi-model-training.timer
    sudo systemctl start harvey-multi-model-training.timer
    
    echo "✅ Service installed and enabled"
ENDSSH

echo ""
echo "🔍 Step 4: Verifying deployment..."
ssh ${USER}@${VM} << 'ENDSSH'
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "Timer Status:"
    echo "═══════════════════════════════════════════════════════════════"
    systemctl list-timers harvey-multi-model-training.timer
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "Service Files:"
    echo "═══════════════════════════════════════════════════════════════"
    ls -lh /home/azureuser/harvey/scripts/multi_model_training_generator.py
ENDSSH

echo ""
echo "=========================================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================================================="
echo ""
echo "📊 Multi-Model Training System:"
echo "   • Schedule: Sunday 5:00 AM UTC"
echo "   • Output: 800 questions/week (200 per model × 4 models)"
echo "   • Models: GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro"
echo ""
echo "🧪 To test manually:"
echo "   ssh ${USER}@${VM}"
echo "   sudo systemctl start harvey-multi-model-training.service"
echo "   sudo journalctl -u harvey-multi-model-training.service -f"
echo ""
echo "🎓 Harvey will learn from 4 AI masters to eventually stand alone!"
echo "=========================================================================="
