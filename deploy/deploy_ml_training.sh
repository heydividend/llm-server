#!/bin/bash
# Deploy ML Training Pipeline to Azure VM
# This script transfers ML training code and runs initial training

set -e

VM_IP="20.81.210.213"
VM_USER="azureuser"
VM_ML_DIR="/home/azureuser/ml-prediction-api"

echo "═══════════════════════════════════════════════════"
echo "🚀 Deploying Harvey ML Training Pipeline to Azure VM"
echo "═══════════════════════════════════════════════════"

# Step 1: Create deployment package
echo "📦 Creating deployment package..."
cd "$(dirname "$0")/.."
tar -czf ml_training_deploy.tar.gz ml_training/

echo "✅ Package created: ml_training_deploy.tar.gz"

# Step 2: Transfer to Azure VM
echo ""
echo "📤 Transferring to Azure VM..."
scp ml_training_deploy.tar.gz ${VM_USER}@${VM_IP}:/tmp/

echo "✅ Transfer complete"

# Step 3: Extract and install on VM
echo ""
echo "📂 Extracting and installing on VM..."
ssh ${VM_USER}@${VM_IP} << 'ENDSSH'
    set -e
    
    echo "Extracting training code..."
    cd /home/azureuser/ml-prediction-api
    tar -xzf /tmp/ml_training_deploy.tar.gz
    rm /tmp/ml_training_deploy.tar.gz
    
    echo "Creating necessary directories..."
    mkdir -p /home/azureuser/ml-prediction-api/models
    mkdir -p /home/azureuser/ml-prediction-api/scripts
    
    # Move training scripts to scripts directory
    if [ -d "/home/azureuser/ml-prediction-api/ml_training" ]; then
        echo "Moving training scripts to scripts directory..."
        cp -r /home/azureuser/ml-prediction-api/ml_training/* /home/azureuser/ml-prediction-api/scripts/
        
        # Keep original ml_training dir as backup
        mv /home/azureuser/ml-prediction-api/ml_training /home/azureuser/ml-prediction-api/ml_training_backup
    fi
    
    echo "Installing Python dependencies..."
    source /home/azureuser/miniconda3/bin/activate
    conda activate llm
    
    # Install ML training requirements
    pip install -r /home/azureuser/ml-prediction-api/scripts/requirements.txt
    
    echo "✅ Installation complete"
ENDSSH

echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ ML Training Pipeline Deployed Successfully!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. SSH to Azure VM:"
echo "   ssh ${VM_USER}@${VM_IP}"
echo ""
echo "2. Run initial training:"
echo "   cd /home/azureuser/ml-prediction-api/scripts"
echo "   conda activate llm"
echo "   python train.py"
echo ""
echo "3. Validate models:"
echo "   python validate.py"
echo ""
echo "4. Check model files created:"
echo "   ls -la /home/azureuser/ml-prediction-api/models/"
echo ""
echo "5. Restart Intelligence Engine to load models:"
echo "   sudo systemctl restart harvey-intelligence.service"
echo ""
echo "6. Verify models loaded:"
echo "   curl http://127.0.0.1:9000/api/internal/ml/health"
echo ""
