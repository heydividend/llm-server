#!/bin/bash
# Run this script ON the Azure VM after uploading the tar.gz file
# Usage: bash INSTALL_ON_AZURE_VM.sh

set -e

echo "=========================================================================="
echo "Harvey Multi-Model Training System - Installation"
echo "=========================================================================="
echo ""

cd /home/azureuser/harvey

echo "📦 Extracting files..."
tar -xzf harvey_multi_model_training.tar.gz

echo "🔧 Installing systemd service..."
sudo cp azure_vm_setup/systemd/harvey-multi-model-training.service /etc/systemd/system/
sudo cp azure_vm_setup/systemd/harvey-multi-model-training.timer /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/harvey-multi-model-training.*

echo "📁 Creating directories..."
mkdir -p training_data

echo "⚙️  Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable harvey-multi-model-training.timer
sudo systemctl start harvey-multi-model-training.timer

echo ""
echo "✅ Installation complete!"
echo ""
systemctl list-timers harvey-multi-model-training.timer

echo ""
echo "=========================================================================="
echo "Multi-Model Training System Installed!"
echo "Schedule: Sunday 5:00 AM UTC"
echo "Output: 800 questions/week from 4 AI models"
echo "=========================================================================="
