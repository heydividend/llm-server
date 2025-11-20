#!/bin/bash
##############################################################################
# Harvey AI - Gemini Training Scheduler Deployment Script
# Deploys automated Gemini training data generation to Azure VM
##############################################################################

set -e

echo "=========================================================================="
echo "  Deploying Gemini Training Scheduler"
echo "=========================================================================="
echo ""

# Configuration
HARVEY_DIR="/home/azureuser/harvey"
LOG_DIR="/var/log/harvey"
SERVICE_NAME="gemini-training-scheduler"

# Step 1: Create log directory
echo "Step 1: Creating log directory..."
sudo mkdir -p "$LOG_DIR"
sudo chown azureuser:azureuser "$LOG_DIR"
echo "✓ Log directory ready: $LOG_DIR"
echo ""

# Step 2: Copy scheduler script
echo "Step 2: Installing scheduler script..."
chmod +x "$HARVEY_DIR/azure_vm_setup/schedulers/gemini_training_scheduler.py"
echo "✓ Scheduler script ready"
echo ""

# Step 3: Install Python dependencies
echo "Step 3: Installing Python dependencies..."
cd "$HARVEY_DIR"
/home/azureuser/miniconda3/bin/pip install schedule python-dotenv google-generativeai --quiet
echo "✓ Dependencies installed"
echo ""

# Step 4: Test prerequisites
echo "Step 4: Testing prerequisites..."
/home/azureuser/miniconda3/bin/python "$HARVEY_DIR/azure_vm_setup/schedulers/gemini_training_scheduler.py" --mode test --count 1
echo "✓ Prerequisites check passed"
echo ""

# Step 5: Install systemd service
echo "Step 5: Installing systemd service..."
sudo cp "$HARVEY_DIR/azure_vm_setup/schedulers/gemini-training-scheduler.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
echo "✓ Systemd service installed"
echo ""

# Step 6: Start the scheduler
echo "Step 6: Starting Gemini Training Scheduler..."
sudo systemctl restart "$SERVICE_NAME"
sleep 3

# Check status
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✓ Gemini Training Scheduler is running"
else
    echo "✗ Scheduler failed to start"
    sudo systemctl status "$SERVICE_NAME" --no-pager -n 20
    exit 1
fi
echo ""

# Step 7: Show scheduler info
echo "=========================================================================="
echo "  ✓ Deployment Complete!"
echo "=========================================================================="
echo ""
echo "Gemini Training Scheduler Status:"
sudo systemctl status "$SERVICE_NAME" --no-pager -n 10
echo ""
echo "Schedule Configuration:"
echo "  - Weekly Generation: Every Sunday at 4:00 AM"
echo "  - Questions per Week: 100 (10 questions per category)"
echo "  - Categories: 10 dividend investing categories"
echo "  - Storage: Saves to training_questions database table"
echo ""
echo "Useful Commands:"
echo "  - Check status:  sudo systemctl status $SERVICE_NAME"
echo "  - View logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "  - Restart:       sudo systemctl restart $SERVICE_NAME"
echo "  - Stop:          sudo systemctl stop $SERVICE_NAME"
echo "  - Test run:      python azure_vm_setup/schedulers/gemini_training_scheduler.py --mode test"
echo "  - Manual run:    python azure_vm_setup/schedulers/gemini_training_scheduler.py --mode once --count 50"
echo ""
echo "Log Files:"
echo "  - Main log:      /var/log/harvey/gemini_training.log"
echo "  - Error log:     /var/log/harvey/gemini_training_error.log"
echo "  - Status file:   /var/log/harvey/gemini_training_status.json"
echo "  - Metrics file:  $HARVEY_DIR/gemini_training_metrics.json"
echo ""
echo "=========================================================================="
