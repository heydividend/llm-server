#!/bin/bash
# Check ML Training Status on Azure VM
# Quick script to verify daily training is working

VM_IP="20.81.210.213"
VM_USER="azureuser"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Harvey ML Training Status Check"
echo "=========================================="
echo ""

# SSH key handling
SSH_KEY=""
if [ "$1" != "" ]; then
    SSH_KEY="-i $1"
fi

ssh ${SSH_KEY} ${VM_USER}@${VM_IP} << 'ENDSSH'
echo "📅 Scheduled Training Status:"
echo "--------------------------------"

# Check systemd timer
if systemctl is-active --quiet harvey-ml-training.timer; then
    echo -e "\033[0;32m✓\033[0m Systemd timer is active"
    echo -n "  Next run: "
    systemctl list-timers harvey-ml-training.timer --no-pager 2>/dev/null | grep harvey-ml | awk '{print $1, $2, $3}'
else
    echo -e "\033[0;31m✗\033[0m Systemd timer is not active"
fi

# Check last service run
echo ""
echo "  Last training run:"
sudo journalctl -u harvey-ml-training.service -n 1 --no-pager 2>/dev/null | tail -1 || echo "    No runs yet"

# Check cron job
echo ""
echo "📋 Cron Backup Status:"
echo "--------------------------------"
if crontab -l 2>/dev/null | grep -q "automated_training.py"; then
    echo -e "\033[0;32m✓\033[0m Cron job is configured"
    crontab -l | grep automated_training.py | sed 's/^/  /'
else
    echo -e "\033[0;31m✗\033[0m No cron job found"
fi

# Check model files
echo ""
echo "🤖 Trained Models:"
echo "--------------------------------"
cd /home/azureuser/harvey/ml_training
if [ -d "models" ]; then
    model_count=$(ls -1 models/*.pkl 2>/dev/null | wc -l)
    if [ "$model_count" -gt 0 ]; then
        echo -e "\033[0;32m✓\033[0m Found $model_count trained models:"
        for model in models/*.pkl; do
            if [ -f "$model" ]; then
                size=$(du -h "$model" | cut -f1)
                age=$(( ($(date +%s) - $(stat -c %Y "$model")) / 86400 ))
                basename=$(basename "$model")
                echo "  • $basename ($size, $age days old)"
            fi
        done
    else
        echo -e "\033[1;33m⚠\033[0m No trained models found"
    fi
else
    echo -e "\033[0;31m✗\033[0m Models directory not found"
fi

# Check ML service status
echo ""
echo "🌐 ML Service Status:"
echo "--------------------------------"
if systemctl is-active --quiet harvey-ml; then
    echo -e "\033[0;32m✓\033[0m ML API service is running"
    # Test the API
    if curl -s -X GET http://localhost:9000/health >/dev/null 2>&1; then
        echo "  API endpoint is responding"
    fi
else
    echo -e "\033[0;31m✗\033[0m ML API service is not running"
fi

echo ""
echo "Use 'sudo journalctl -u harvey-ml-training -f' to watch training logs"
ENDSSH