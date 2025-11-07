#!/bin/bash
# Sync ML Training Code from Replit to Azure VM
# Maintains code consistency between development and production

set -e

echo "=========================================="
echo "Sync Harvey ML Code to Azure VM"
echo "=========================================="

# Configuration
VM_IP="20.81.210.213"
VM_USER="azureuser"  # Updated with correct username
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
if [ "$1" != "" ]; then
    SSH_KEY="-i $1"
fi

# Function to sync files
sync_files() {
    print_status "Starting file sync to Azure VM..."
    
    # Sync ML training directory
    print_status "Syncing ML training files..."
    rsync -avz --delete \
        ${SSH_KEY} \
        --exclude='venv/' \
        --exclude='*.pyc' \
        --exclude='__pycache__/' \
        --exclude='models/*.pkl' \
        --exclude='*.log' \
        ml_training/ ${VM_USER}@${VM_IP}:${REMOTE_DIR}/ml_training/
    
    # Sync Azure VM setup scripts
    print_status "Syncing setup scripts..."
    rsync -avz \
        ${SSH_KEY} \
        azure_vm_setup/ ${VM_USER}@${VM_IP}:${REMOTE_DIR}/azure_vm_setup/
    
    # Sync app services (ML client updates)
    print_status "Syncing app services..."
    rsync -avz \
        ${SSH_KEY} \
        app/services/ml_api_client.py ${VM_USER}@${VM_IP}:${REMOTE_DIR}/app/services/
    rsync -avz \
        ${SSH_KEY} \
        app/services/ml_integration.py ${VM_USER}@${VM_IP}:${REMOTE_DIR}/app/services/
}

# Function to restart services
restart_services() {
    print_status "Restarting services on Azure VM..."
    
    ssh ${SSH_KEY} ${VM_USER}@${VM_IP} << 'ENDSSH'
    # Check if services exist
    if systemctl list-units --all | grep -q harvey-ml.service; then
        echo "Restarting harvey-ml service..."
        sudo systemctl restart harvey-ml
        sleep 2
        systemctl is-active --quiet harvey-ml && echo "✓ harvey-ml is running" || echo "✗ harvey-ml failed to start"
    fi
    
    if systemctl list-units --all | grep -q harvey-backend.service; then
        echo "Restarting harvey-backend service..."
        sudo systemctl restart harvey-backend
        sleep 2
        systemctl is-active --quiet harvey-backend && echo "✓ harvey-backend is running" || echo "✗ harvey-backend failed to start"
    fi
ENDSSH
}

# Main execution
echo ""
echo "This will sync the following from Replit to Azure VM:"
echo "  • ML training code (ml_training/)"
echo "  • Setup scripts (azure_vm_setup/)"
echo "  • ML API client updates (app/services/)"
echo ""
echo "Target: ${VM_USER}@${VM_IP}:${REMOTE_DIR}"
echo ""

read -p "Continue with sync? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Sync cancelled"
    exit 1
fi

# Test SSH connection
print_status "Testing SSH connection..."
if ! ssh ${SSH_KEY} ${VM_USER}@${VM_IP} "echo 'Connected'" 2>/dev/null; then
    print_error "Failed to connect to Azure VM"
    echo ""
    echo "Usage:"
    echo "  With SSH key: bash azure_vm_setup/sync_to_vm.sh ~/.ssh/your-key.pem"
    echo "  Without key:  bash azure_vm_setup/sync_to_vm.sh"
    exit 1
fi

# Perform sync
sync_files

# Ask about service restart
echo ""
read -p "Do you want to restart ML services? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    restart_services
fi

# Show completion message
echo ""
echo "=========================================="
echo "Sync Complete!"
echo "=========================================="
echo ""
echo "Next steps on Azure VM:"
echo "1. SSH into VM: ssh ${SSH_KEY} ${VM_USER}@${VM_IP}"
echo "2. Navigate to: cd ${REMOTE_DIR}/ml_training"
echo "3. Activate venv: source venv/bin/activate"
echo "4. Train models: python train.py --model all --save-dir ./models"
echo ""
echo "The data_extraction.py file has been fixed and synced!"
echo "Training should now work with pymssql."