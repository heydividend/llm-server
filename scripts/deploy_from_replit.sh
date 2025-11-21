#!/bin/bash

# Harvey AI - Simple Deploy from Replit to Azure VM
# Usage: ./scripts/deploy_from_replit.sh

set -e

# Hardcoded Azure VM details
AZURE_VM_IP="20.81.210.213"
AZURE_VM_USER="azureuser"
HARVEY_DIR="/home/azureuser/harvey"

echo "🚀 Deploying Harvey to Azure VM..."
echo ""

# Step 1: Push to git
echo "📤 Step 1: Pushing to git..."
git push origin main
echo "✅ Pushed to git"
echo ""

# Step 2: Copy deployment script to VM
echo "📤 Step 2: Copying deployment script to VM..."
scp deploy_on_azure_vm.sh $AZURE_VM_USER@$AZURE_VM_IP:$HARVEY_DIR/
echo "✅ Script copied"
echo ""

# Step 3: Run deployment on VM
echo "🚀 Step 3: Running deployment on VM..."
ssh $AZURE_VM_USER@$AZURE_VM_IP "cd $HARVEY_DIR && chmod +x deploy_on_azure_vm.sh && ./deploy_on_azure_vm.sh"
echo ""

echo "✅ Deployment complete!"
echo "🌐 Harvey URL: http://$AZURE_VM_IP:8001"
