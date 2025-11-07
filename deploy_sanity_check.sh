#!/bin/bash

# Deploy Sanity Check Script to Azure VM

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"
REMOTE_DIR="/home/azureuser/harvey"

echo "=================================================="
echo "🚀 Deploying Sanity Check Script to Azure VM"
echo "=================================================="
echo ""

# Copy the sanity check script
echo "📤 Copying sanity check script to Azure VM..."
echo "You'll be prompted for password:"
scp harvey_sanity_check.py $AZURE_USER@$AZURE_VM_IP:$REMOTE_DIR/

if [ $? -eq 0 ]; then
    echo "✅ Script deployed successfully!"
    echo ""
    echo "=================================================="
    echo "📋 TO RUN THE SANITY CHECK ON AZURE VM:"
    echo "=================================================="
    echo ""
    echo "1. SSH into the VM:"
    echo "   ssh $AZURE_USER@$AZURE_VM_IP"
    echo ""
    echo "2. Navigate to Harvey directory:"
    echo "   cd $REMOTE_DIR"
    echo ""
    echo "3. Run the sanity check:"
    echo "   python harvey_sanity_check.py"
    echo ""
    echo "The script will check:"
    echo "  ✓ Environment variables (database, API keys)"
    echo "  ✓ Python packages installation"
    echo "  ✓ Database connectivity and write permissions"
    echo "  ✓ ML Service availability"
    echo "  ✓ Harvey API endpoints"
    echo "  ✓ ML Scheduler services"
    echo "  ✓ Network connectivity"
    echo ""
    echo "A detailed report will be saved as:"
    echo "  sanity_check_report_<timestamp>.json"
    echo "=================================================="
else
    echo "❌ Failed to deploy script. Please check your connection."
    exit 1
fi