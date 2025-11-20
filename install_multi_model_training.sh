#!/bin/bash
# Harvey Multi-Model Training System - Install Script
# Run this script ON the Azure VM after git pull
# Usage: ssh azureuser@20.81.210.213 then run: bash install_multi_model_training.sh

set -e

HARVEY_DIR="/home/azureuser/harvey"

echo "=========================================================================="
echo "🚀 Harvey Multi-Model Training System - Installation"
echo "=========================================================================="
echo ""

# Step 1: Pull latest code
echo "📥 Step 1: Pulling latest code from git..."
cd $HARVEY_DIR
git pull

echo "   ✅ Code updated"
echo ""

# Step 2: Install systemd service
echo "🔧 Step 2: Installing systemd service and timer..."
sudo cp azure_vm_setup/systemd/harvey-multi-model-training.service /etc/systemd/system/
sudo cp azure_vm_setup/systemd/harvey-multi-model-training.timer /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.*

echo "   ✅ Systemd files installed"
echo ""

# Step 3: Create directories
echo "📁 Step 3: Creating training data directory..."
mkdir -p $HARVEY_DIR/training_data

echo "   ✅ Directory created"
echo ""

# Step 4: Reload and enable service
echo "⚙️  Step 4: Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable harvey-multi-model-training.timer
sudo systemctl start harvey-multi-model-training.timer

echo "   ✅ Service enabled and started"
echo ""

# Step 5: Verify deployment
echo "🔍 Step 5: Verifying deployment..."
echo ""

echo "══════════════════════════════════════════════════════════════════════"
echo "Timer Status:"
echo "══════════════════════════════════════════════════════════════════════"
systemctl status harvey-multi-model-training.timer --no-pager | head -10

echo ""
echo "══════════════════════════════════════════════════════════════════════"
echo "Next Scheduled Run:"
echo "══════════════════════════════════════════════════════════════════════"
systemctl list-timers harvey-multi-model-training.timer --no-pager

echo ""
echo "══════════════════════════════════════════════════════════════════════"
echo "Generator Script:"
echo "══════════════════════════════════════════════════════════════════════"
ls -lh $HARVEY_DIR/scripts/multi_model_training_generator.py

echo ""
echo "=========================================================================="
echo "✅ INSTALLATION COMPLETE!"
echo "=========================================================================="
echo ""
echo "📊 Multi-Model Training System:"
echo "   • Script: $HARVEY_DIR/scripts/multi_model_training_generator.py"
echo "   • Schedule: Sunday 5:00 AM UTC"
echo "   • Output: 800 questions/week (200 per model × 4 models)"
echo "   • Models: GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro"
echo ""
echo "🧪 To test manually:"
echo "   sudo systemctl start harvey-multi-model-training.service"
echo "   sudo journalctl -u harvey-multi-model-training.service -f"
echo ""
echo "📋 To check logs later:"
echo "   sudo journalctl -u harvey-multi-model-training.service -n 50"
echo ""
echo "🎓 Harvey will learn from 4 AI masters to eventually stand alone!"
echo "=========================================================================="
