#!/bin/bash
# Harvey Intelligence Engine - Training Automation Setup
# Run this script on Azure VM to set up nightly training automation

set -e

echo "═══════════════════════════════════════════════════"
echo "🤖 Harvey Intelligence Engine - Training Automation Setup"
echo "═══════════════════════════════════════════════════"
echo ""

# Check if running on Azure VM
if [ ! -d "/home/azureuser" ]; then
    echo "❌ Error: This script must be run on the Azure VM"
    exit 1
fi

# Step 1: Create directories
echo "📁 Creating directories..."
sudo mkdir -p /opt/harvey-intelligence
sudo mkdir -p /var/log/harvey-intelligence
sudo mkdir -p /opt/harvey-intelligence/model-backups

# Set permissions
sudo chown -R azureuser:azureuser /opt/harvey-intelligence
sudo chown -R azureuser:azureuser /var/log/harvey-intelligence

# Step 2: Copy training script
echo "📝 Installing training script..."
sudo cp train_daily.sh /opt/harvey-intelligence/train_daily.sh
sudo chmod +x /opt/harvey-intelligence/train_daily.sh
sudo chown azureuser:azureuser /opt/harvey-intelligence/train_daily.sh

# Step 3: Install systemd service
echo "⚙️  Installing systemd service..."
sudo cp harvey-training.service /etc/systemd/system/harvey-training.service

# Step 4: Install systemd timer
echo "⏰ Installing systemd timer..."
sudo cp harvey-training.timer /etc/systemd/system/harvey-training.timer

# Step 5: Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Step 6: Enable and start timer
echo "▶️  Enabling timer..."
sudo systemctl enable harvey-training.timer
sudo systemctl start harvey-training.timer

# Step 7: Display status
echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ TRAINING AUTOMATION SETUP COMPLETE"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Timer Status:"
sudo systemctl status harvey-training.timer --no-pager || true
echo ""
echo "Next scheduled run:"
sudo systemctl list-timers harvey-training.timer --no-pager || true
echo ""
echo "═══════════════════════════════════════════════════"
echo "📖 Management Commands:"
echo "═══════════════════════════════════════════════════"
echo ""
echo "View timer status:"
echo "  sudo systemctl status harvey-training.timer"
echo ""
echo "View next scheduled runs:"
echo "  sudo systemctl list-timers --all | grep harvey"
echo ""
echo "Trigger training manually:"
echo "  sudo systemctl start harvey-training.service"
echo ""
echo "View training logs:"
echo "  sudo journalctl -u harvey-training.service -f"
echo "  tail -f /var/log/harvey-intelligence/training-*.log"
echo ""
echo "Disable automatic training:"
echo "  sudo systemctl stop harvey-training.timer"
echo "  sudo systemctl disable harvey-training.timer"
echo ""
echo "═══════════════════════════════════════════════════"
echo "🔔 Optional: Slack Notifications"
echo "═══════════════════════════════════════════════════"
echo ""
echo "To enable Slack alerts, add to /etc/environment:"
echo "  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
echo ""
echo "Then reload:"
echo "  sudo systemctl daemon-reload"
echo ""
echo "═══════════════════════════════════════════════════"
