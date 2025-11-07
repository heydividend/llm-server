#!/bin/bash
# Quick sync script - simpler alternative without rsync
# Just syncs the critical ML training files

VM_IP="20.81.210.213"
VM_USER="azureuser"

echo "Quick Sync: ML Training Files to Azure VM"
echo "=========================================="

# Copy the fixed data_extraction.py file
echo "Copying fixed data_extraction.py..."
scp ml_training/data_extraction.py ${VM_USER}@${VM_IP}:/home/azureuser/harvey/ml_training/

# Copy all model files (in case they were updated)
echo "Copying model definitions..."
scp ml_training/models/*.py ${VM_USER}@${VM_IP}:/home/azureuser/harvey/ml_training/models/

# Copy training scripts
echo "Copying training scripts..."
scp ml_training/train.py ${VM_USER}@${VM_IP}:/home/azureuser/harvey/ml_training/
scp ml_training/validate.py ${VM_USER}@${VM_IP}:/home/azureuser/harvey/ml_training/

echo ""
echo "✅ Files synced successfully!"
echo ""
echo "Now SSH into your VM and run:"
echo "  cd /home/azureuser/harvey/ml_training"
echo "  source venv/bin/activate"
echo "  python train.py --model all --save-dir ./models"