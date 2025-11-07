#!/bin/bash
# Deploy ML Training Updates from Replit to Azure VM
# Run this from your local machine or Replit

set -e

echo "=========================================="
echo "Deploy ML Training to Azure VM"
echo "=========================================="

# Configuration
VM_IP="20.81.210.213"
VM_USER="harvey"  # Update with your VM username
LOCAL_DIR="."  # Current directory (Replit project)
REMOTE_DIR="/home/harvey/harvey-backend"

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
if [ "$1" == "" ]; then
    print_warning "No SSH key specified, using default SSH settings"
    SSH_CMD="ssh ${VM_USER}@${VM_IP}"
    SCP_CMD="scp -r"
else
    SSH_KEY=$1
    SSH_CMD="ssh -i ${SSH_KEY} ${VM_USER}@${VM_IP}"
    SCP_CMD="scp -i ${SSH_KEY} -r"
fi

# Test SSH connection
print_status "Testing SSH connection to ${VM_IP}..."
if ! ${SSH_CMD} "echo 'Connection successful'" 2>/dev/null; then
    print_error "Failed to connect to Azure VM"
    echo "Please check:"
    echo "  1. VM IP address: ${VM_IP}"
    echo "  2. Username: ${VM_USER}"
    echo "  3. SSH key (if using): ${SSH_KEY}"
    exit 1
fi

# 1. Copy ML training files
print_status "Copying ML training files..."
${SCP_CMD} ml_training/* ${VM_USER}@${VM_IP}:${REMOTE_DIR}/ml_training/

# 2. Copy setup scripts
print_status "Copying setup scripts..."
${SCP_CMD} azure_vm_setup/* ${VM_USER}@${VM_IP}:${REMOTE_DIR}/azure_vm_setup/

# 3. Copy updated API files (if changed)
print_status "Copying updated API files..."
${SCP_CMD} app/services/ml_api_client.py ${VM_USER}@${VM_IP}:${REMOTE_DIR}/app/services/
${SCP_CMD} app/services/ml_integration.py ${VM_USER}@${VM_IP}:${REMOTE_DIR}/app/services/

# 4. Set permissions on VM
print_status "Setting permissions on VM..."
${SSH_CMD} << 'ENDSSH'
cd /home/harvey/harvey-backend
chmod +x azure_vm_setup/*.sh
chmod +x azure_vm_setup/*.py
chmod +x ml_training/*.py

# Create models directory if it doesn't exist
mkdir -p ml_training/models

# Set ownership
chown -R harvey:harvey ml_training/
chown -R harvey:harvey azure_vm_setup/
ENDSSH

# 5. Check if setup is needed
print_status "Checking VM setup status..."
SETUP_NEEDED=$(${SSH_CMD} "if [ -f /etc/systemd/system/harvey-ml-training.service ]; then echo 'false'; else echo 'true'; fi")

if [ "$SETUP_NEEDED" == "true" ]; then
    print_warning "Continuous training not set up on VM"
    echo ""
    read -p "Do you want to run the setup script now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Running setup script on VM..."
        ${SSH_CMD} "cd ${REMOTE_DIR} && sudo bash azure_vm_setup/setup_continuous_training.sh"
    else
        echo ""
        echo "To set up continuous training later, SSH into the VM and run:"
        echo "  cd ${REMOTE_DIR}"
        echo "  sudo bash azure_vm_setup/setup_continuous_training.sh"
    fi
else
    print_status "Continuous training service already installed"
    
    # Restart services to load new code
    read -p "Do you want to restart ML services to load updates? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Restarting services..."
        ${SSH_CMD} << 'ENDSSH'
        sudo systemctl restart harvey-ml
        sudo systemctl restart harvey-ml-training
        
        # Check status
        echo ""
        echo "Service Status:"
        systemctl is-active harvey-ml && echo "  harvey-ml: Active" || echo "  harvey-ml: Inactive"
        systemctl is-active harvey-ml-training && echo "  harvey-ml-training: Active" || echo "  harvey-ml-training: Inactive"
ENDSSH
    fi
fi

# 6. Show current model status
print_status "Current ML Model Status on VM:"
${SSH_CMD} "cd ${REMOTE_DIR}/ml_training && python3 monitor_training.py 2>/dev/null || echo 'Monitor script not yet available'"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. SSH into VM: ssh ${VM_USER}@${VM_IP}"
echo "2. Check training status: harvey-ml-monitor"
echo "3. Trigger manual training: harvey-ml-monitor --train all"
echo "4. Watch training logs: harvey-ml-monitor --watch"
echo ""
echo "For continuous training setup (if not done):"
echo "  sudo bash ${REMOTE_DIR}/azure_vm_setup/setup_continuous_training.sh"