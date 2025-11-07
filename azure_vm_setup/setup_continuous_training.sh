#!/bin/bash
# Harvey ML Continuous Training Setup Script
# Run this on the Azure VM to set up automated ML training

set -e

echo "=========================================="
echo "Harvey ML Continuous Training Setup"
echo "=========================================="

# Variables (update these as needed)
HARVEY_USER="harvey"
HARVEY_HOME="/home/harvey"
PROJECT_DIR="${HARVEY_HOME}/harvey-backend"
ML_TRAINING_DIR="${PROJECT_DIR}/ml_training"
SETUP_DIR="${PROJECT_DIR}/azure_vm_setup"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
   print_error "Please run as root or with sudo"
   exit 1
fi

# 1. Create necessary directories
print_status "Creating directories..."
mkdir -p /var/log/harvey
chown ${HARVEY_USER}:${HARVEY_USER} /var/log/harvey
chmod 755 /var/log/harvey

# 2. Install Python dependencies
print_status "Installing Python dependencies..."
cd ${ML_TRAINING_DIR}

# Check if virtual environment exists
if [ -d "venv" ]; then
    print_status "Activating existing virtual environment..."
    source venv/bin/activate
else
    print_status "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install training dependencies
pip install --upgrade pip
pip install schedule tabulate colorama

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_warning "requirements.txt not found, installing base packages..."
    pip install pandas numpy scikit-learn joblib sqlalchemy pymssql pyodbc
fi

deactivate

# 3. Copy automated training script
print_status "Setting up automated training script..."
if [ -f "${SETUP_DIR}/automated_training.py" ]; then
    cp ${SETUP_DIR}/automated_training.py ${ML_TRAINING_DIR}/
    chmod +x ${ML_TRAINING_DIR}/automated_training.py
    chown ${HARVEY_USER}:${HARVEY_USER} ${ML_TRAINING_DIR}/automated_training.py
else
    print_error "automated_training.py not found in ${SETUP_DIR}"
fi

# 4. Copy monitoring script
print_status "Setting up monitoring script..."
if [ -f "${SETUP_DIR}/monitor_training.py" ]; then
    cp ${SETUP_DIR}/monitor_training.py ${ML_TRAINING_DIR}/
    chmod +x ${ML_TRAINING_DIR}/monitor_training.py
    chown ${HARVEY_USER}:${HARVEY_USER} ${ML_TRAINING_DIR}/monitor_training.py
    
    # Create symlink for easy access
    ln -sf ${ML_TRAINING_DIR}/monitor_training.py /usr/local/bin/harvey-ml-monitor
else
    print_error "monitor_training.py not found in ${SETUP_DIR}"
fi

# 5. Install systemd service
print_status "Installing systemd service..."
if [ -f "${SETUP_DIR}/harvey-ml-training.service" ]; then
    cp ${SETUP_DIR}/harvey-ml-training.service /etc/systemd/system/
    
    # Update paths in service file
    sed -i "s|/home/harvey|${HARVEY_HOME}|g" /etc/systemd/system/harvey-ml-training.service
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Systemd service installed"
else
    print_error "harvey-ml-training.service not found"
fi

# 6. Create cron job for backup training (optional)
print_status "Setting up cron backup..."
CRON_JOB="0 3 * * * ${HARVEY_USER} cd ${ML_TRAINING_DIR} && /usr/bin/python3 automated_training.py --mode once >> /var/log/harvey/cron_training.log 2>&1"

# Check if cron job already exists
if ! crontab -l -u ${HARVEY_USER} 2>/dev/null | grep -q "automated_training.py"; then
    (crontab -l -u ${HARVEY_USER} 2>/dev/null; echo "$CRON_JOB") | crontab -u ${HARVEY_USER} -
    print_status "Cron backup job added"
else
    print_status "Cron job already exists"
fi

# 7. Run initial training
read -p "Do you want to run initial training now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting initial training..."
    su - ${HARVEY_USER} -c "cd ${ML_TRAINING_DIR} && python3 automated_training.py --mode once"
fi

# 8. Start the training service
read -p "Do you want to start the continuous training service? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting training service..."
    systemctl enable harvey-ml-training
    systemctl start harvey-ml-training
    
    # Check status
    sleep 5
    if systemctl is-active --quiet harvey-ml-training; then
        print_status "Training service is running"
    else
        print_error "Training service failed to start"
        echo "Check logs with: journalctl -u harvey-ml-training -n 50"
    fi
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  - Check status:    harvey-ml-monitor"
echo "  - Watch logs:      harvey-ml-monitor --watch"
echo "  - Trigger training: harvey-ml-monitor --train all"
echo "  - Service status:  systemctl status harvey-ml-training"
echo "  - Service logs:    journalctl -u harvey-ml-training -f"
echo ""
echo "Training Schedule:"
echo "  - Full training: Daily at 2:00 AM"
echo "  - Incremental: Every 6 hours"
echo "  - Validation: Every 12 hours"
echo "  - Backup (cron): Daily at 3:00 AM"
echo ""

# 9. Display current status
print_status "Current Model Status:"
if [ -x "${ML_TRAINING_DIR}/monitor_training.py" ]; then
    python3 ${ML_TRAINING_DIR}/monitor_training.py
fi