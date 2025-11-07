#!/bin/bash
# Deploy and Schedule Daily ML Training on Azure VM
# This script sets up automated daily training for Harvey ML models

set -e

echo "=========================================="
echo "Deploy Daily ML Training to Azure VM"
echo "=========================================="

# Configuration
VM_IP="20.81.210.213"
VM_USER="azureuser"
REMOTE_DIR="/home/azureuser/harvey"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if SSH key is provided
SSH_KEY=""
SCP_KEY=""
if [ "$1" != "" ]; then
    SSH_KEY="-i $1"
    SCP_KEY="-i $1"
fi

# Test SSH connection
print_status "Testing connection to Azure VM..."
if ! ssh ${SSH_KEY} ${VM_USER}@${VM_IP} "echo 'Connected'" 2>/dev/null; then
    print_error "Failed to connect to Azure VM"
    echo "Usage: bash deploy_daily_training.sh [path-to-ssh-key]"
    exit 1
fi

# Step 1: Sync all ML training files
print_status "Syncing ML training files..."
scp ${SCP_KEY} -r ml_training/* ${VM_USER}@${VM_IP}:${REMOTE_DIR}/ml_training/ 2>/dev/null || true
scp ${SCP_KEY} azure_vm_setup/automated_training.py ${VM_USER}@${VM_IP}:${REMOTE_DIR}/ml_training/
scp ${SCP_KEY} azure_vm_setup/monitor_training.py ${VM_USER}@${VM_IP}:${REMOTE_DIR}/ml_training/

# Step 2: Create systemd service and timer files locally
print_status "Creating systemd configuration..."

# Create the service file
cat > /tmp/harvey-ml-training.service << 'EOF'
[Unit]
Description=Harvey ML Model Training
After=network.target

[Service]
Type=oneshot
User=azureuser
WorkingDirectory=/home/azureuser/harvey/ml_training
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="USE_PYMSSQL=true"
Environment="PYTHONPATH=/home/azureuser/harvey"
ExecStartPre=/bin/bash -c 'echo "Starting ML training with pymssql driver..."'
ExecStart=/bin/bash -c 'source /home/azureuser/harvey/ml_training/venv/bin/activate && export USE_PYMSSQL=true && python /home/azureuser/harvey/ml_training/train.py --model all --save-dir ./models'
ExecStartPost=/bin/bash -c 'echo "ML training completed. Restarting ML service..." && sudo systemctl restart harvey-ml'

# Logging
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryLimit=4G
CPUQuota=75%

[Install]
WantedBy=multi-user.target
EOF

# Create the timer file for daily execution
cat > /tmp/harvey-ml-training.timer << 'EOF'
[Unit]
Description=Daily Harvey ML Model Training
Requires=harvey-ml-training.service

[Timer]
# Run daily at 2 AM
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
# Run on startup if missed
Persistent=true
# Randomize by up to 30 minutes to avoid load spikes
RandomizedDelaySec=1800

[Install]
WantedBy=timers.target
EOF

# Step 3: Deploy and configure on VM
print_status "Deploying to Azure VM..."

ssh ${SSH_KEY} ${VM_USER}@${VM_IP} << 'ENDSSH'
# Create necessary directories
sudo mkdir -p /var/log/harvey
sudo chown azureuser:azureuser /var/log/harvey

# Ensure virtual environment exists
cd /home/azureuser/harvey/ml_training
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install pandas numpy scikit-learn xgboost lightgbm joblib sqlalchemy pymssql scipy matplotlib seaborn schedule tabulate colorama
    deactivate
fi

# Make scripts executable
chmod +x automated_training.py
chmod +x monitor_training.py

# Test that training script works
echo "Testing training script..."
export USE_PYMSSQL=true
source venv/bin/activate
python -c "from data_extraction import DataExtractor; print('✓ Database connection OK')" || exit 1
deactivate
ENDSSH

# Step 4: Copy systemd files to VM and install them
print_status "Installing systemd service and timer..."
scp ${SCP_KEY} /tmp/harvey-ml-training.service ${VM_USER}@${VM_IP}:/tmp/
scp ${SCP_KEY} /tmp/harvey-ml-training.timer ${VM_USER}@${VM_IP}:/tmp/

ssh ${SSH_KEY} ${VM_USER}@${VM_IP} << 'ENDSSH'
# Install systemd files
sudo mv /tmp/harvey-ml-training.service /etc/systemd/system/
sudo mv /tmp/harvey-ml-training.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the timer
sudo systemctl enable harvey-ml-training.timer
sudo systemctl start harvey-ml-training.timer

# Check status
echo ""
echo "Checking timer status..."
sudo systemctl status harvey-ml-training.timer --no-pager
echo ""
echo "Next scheduled run:"
sudo systemctl list-timers harvey-ml-training.timer --no-pager
ENDSSH

# Step 5: Set up cron backup (optional redundancy)
print_status "Setting up cron backup..."
ssh ${SSH_KEY} ${VM_USER}@${VM_IP} << 'ENDSSH'
# Add cron job as backup
CRON_LINE="0 3 * * * cd /home/azureuser/harvey/ml_training && source venv/bin/activate && export USE_PYMSSQL=true && python automated_training.py --mode once >> /var/log/harvey/cron_training.log 2>&1"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "automated_training.py"; then
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "✓ Cron backup job added (runs at 3 AM daily)"
else
    echo "✓ Cron job already exists"
fi

# Show current crontab
echo ""
echo "Current cron jobs:"
crontab -l | grep harvey || echo "No Harvey cron jobs found"
ENDSSH

# Step 6: Run initial training (optional)
echo ""
read -p "Do you want to run initial training now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Running initial training..."
    ssh ${SSH_KEY} ${VM_USER}@${VM_IP} << 'ENDSSH'
    cd /home/azureuser/harvey/ml_training
    source venv/bin/activate
    export USE_PYMSSQL=true
    python train.py --model all --save-dir ./models
    deactivate
ENDSSH
fi

# Clean up temp files
rm -f /tmp/harvey-ml-training.service /tmp/harvey-ml-training.timer

# Final status
echo ""
echo "=========================================="
echo "✅ Daily Training Setup Complete!"
echo "=========================================="
echo ""
echo "📅 Training Schedule:"
echo "  • Systemd Timer: Daily at 2:00 AM"
echo "  • Cron Backup: Daily at 3:00 AM"
echo ""
echo "📊 Useful Commands (run on VM):"
echo "  • Check timer: sudo systemctl status harvey-ml-training.timer"
echo "  • Next run: sudo systemctl list-timers harvey-ml-training"
echo "  • Run manually: sudo systemctl start harvey-ml-training.service"
echo "  • View logs: sudo journalctl -u harvey-ml-training -f"
echo "  • Monitor status: python ${REMOTE_DIR}/ml_training/monitor_training.py"
echo ""
echo "🔄 Models will now train automatically every day!"