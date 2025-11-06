#!/bin/bash

# Quick Deploy Script for Harvey to Azure VM
# Run this from your Replit terminal

echo "🚀 Harvey Quick Deploy to Azure VM (20.81.210.213)"
echo "=================================================="

# Variables
VM_IP="20.81.210.213"
VM_USER="azureuser"
HARVEY_DIR="/home/azureuser/harvey"

echo "📦 Step 1: Syncing code to Azure VM..."
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pythonlibs' \
    --exclude='logs' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    ./ ${VM_USER}@${VM_IP}:${HARVEY_DIR}/

echo ""
echo "🔧 Step 2: Restarting services on Azure VM..."
ssh ${VM_USER}@${VM_IP} << 'EOF'
    echo "Installing dependencies..."
    cd /home/azureuser/harvey
    pip install -q -r requirements.txt
    
    echo "Restarting Harvey services..."
    sudo systemctl restart harvey-backend
    sudo systemctl restart harvey-ml
    
    echo "Checking service status..."
    sleep 3
    systemctl is-active harvey-backend && echo "✓ Backend running" || echo "✗ Backend failed"
    systemctl is-active harvey-ml && echo "✓ ML API running" || echo "✗ ML API failed"
EOF

echo ""
echo "✅ Step 3: Testing deployment..."
echo "Testing backend health..."
curl -s http://${VM_IP}:8000/health > /dev/null 2>&1 && echo "✓ Backend accessible" || echo "✗ Backend not accessible"

echo "Testing Harvey Intelligence..."
curl -s -X POST http://${VM_IP}:8000/v1/harvey/analyze \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' > /dev/null 2>&1 && echo "✓ Harvey Intelligence working" || echo "✗ Harvey Intelligence failed"

echo ""
echo "=================================================="
echo "🎉 Deployment complete!"
echo "Production URL: http://${VM_IP}:8000"
echo "Admin Status: http://${VM_IP}:8000/v1/admin/status"
echo "=================================================="