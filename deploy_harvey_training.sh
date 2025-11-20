#!/bin/bash
# Harvey Multi-Model Training System - Complete Deployment Script
# This script does everything: commit, push, deploy, and verify

set -e

echo "=========================================================================="
echo "🚀 Harvey Multi-Model Training System - Complete Deployment"
echo "=========================================================================="
echo ""

# Step 1: Commit and push changes
echo "📝 Step 1: Committing changes to git..."
git add scripts/multi_model_training_generator.py \
  azure_vm_setup/systemd/harvey-multi-model-training.service \
  azure_vm_setup/systemd/harvey-multi-model-training.timer \
  MULTI_MODEL_TRAINING_ARCHITECTURE.md \
  SIMPLE_DEPLOYMENT.md \
  replit.md

git commit -m "feat: Multi-model training system - Harvey learns from 4 AI masters

- Multi-model training generator using GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro
- Generates 800 questions/week (8x increase in training diversity)
- Systemd service/timer for Sunday 5:00 AM automated runs
- Fixed paths to use /opt/harvey
- Vision: Train Harvey until it stands alone" || echo "   ⚠️  No changes to commit or already committed"

echo "   → Pushing to remote..."
git push origin main || git push origin master || echo "   ⚠️  Push failed, continuing anyway..."

echo "   ✅ Git operations complete"
echo ""

# Step 2: Deploy to Azure VM
echo "🔐 Step 2: Deploying to Azure VM..."
echo "   Target: $AZURE_VM_USER@$AZURE_VM_IP"
echo ""

ssh $AZURE_VM_USER@$AZURE_VM_IP << 'DEPLOY_SCRIPT'
    set -e
    
    echo "   📥 Pulling latest code..."
    cd /opt/harvey
    git pull
    
    echo "   🔧 Installing systemd service..."
    sudo cp azure_vm_setup/systemd/harvey-multi-model-training.service /etc/systemd/system/
    sudo cp azure_vm_setup/systemd/harvey-multi-model-training.timer /etc/systemd/system/
    sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.*
    
    echo "   📁 Creating directories..."
    mkdir -p training_data
    
    echo "   ⚙️  Enabling and starting service..."
    sudo systemctl daemon-reload
    sudo systemctl enable harvey-multi-model-training.timer
    sudo systemctl start harvey-multi-model-training.timer
    
    echo ""
    echo "   ✅ Deployment complete!"
DEPLOY_SCRIPT

echo ""
echo "🔍 Step 3: Verifying deployment..."

ssh $AZURE_VM_USER@$AZURE_VM_IP << 'VERIFY_SCRIPT'
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "Timer Status:"
    echo "═══════════════════════════════════════════════════════════════════════"
    systemctl status harvey-multi-model-training.timer --no-pager | head -10
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "Next Scheduled Run:"
    echo "═══════════════════════════════════════════════════════════════════════"
    systemctl list-timers harvey-multi-model-training.timer --no-pager
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "Generator Script:"
    echo "═══════════════════════════════════════════════════════════════════════"
    ls -lh /opt/harvey/scripts/multi_model_training_generator.py
VERIFY_SCRIPT

echo ""
echo "=========================================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================================================="
echo ""
echo "📊 Multi-Model Training System Status:"
echo "   • Generator: /opt/harvey/scripts/multi_model_training_generator.py"
echo "   • Schedule: Sunday 5:00 AM UTC"
echo "   • Output: 800 questions/week (200 per model × 4 models)"
echo "   • Models: GPT-5, Grok-4, DeepSeek-R1, Gemini 2.5 Pro"
echo ""
echo "🧪 To test manually:"
echo "   ssh $AZURE_VM_USER@$AZURE_VM_IP"
echo "   sudo systemctl start harvey-multi-model-training.service"
echo "   sudo journalctl -u harvey-multi-model-training.service -f"
echo ""
echo "🎓 Harvey will learn from 4 AI masters to eventually stand alone!"
echo "=========================================================================="
