#!/bin/bash
# Harvey Intelligence Engine - Rename ML API Service
# Run this script on Azure VM (20.81.210.213) to rename ml-api to harvey-intelligence

set -e

echo "🔄 Renaming ML API to Harvey Intelligence Engine..."

# Step 1: Stop current ml-api service
echo "Stopping ml-api service..."
sudo systemctl stop ml-api.service

# Step 2: Create new harvey-intelligence service
echo "Creating harvey-intelligence.service..."
sudo tee /etc/systemd/system/harvey-intelligence.service > /dev/null << 'EOF'
[Unit]
Description=Harvey Intelligence Engine - ML Prediction Service
After=network.target

[Service]
Type=simple
User=azureuser
Group=azureuser
WorkingDirectory=/home/azureuser/ml-prediction-api
Environment="PATH=/home/azureuser/miniconda3/envs/llm/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/azureuser/miniconda3/envs/llm/bin/python -m uvicorn main:app --host 127.0.0.1 --port 9000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Step 3: Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Step 4: Enable new service
echo "Enabling harvey-intelligence.service..."
sudo systemctl enable harvey-intelligence.service

# Step 5: Disable and remove old service
echo "Disabling ml-api.service..."
sudo systemctl disable ml-api.service || true
sudo rm -f /etc/systemd/system/ml-api.service

# Step 6: Start new service
echo "Starting harvey-intelligence.service..."
sudo systemctl start harvey-intelligence.service

# Step 7: Wait and verify
sleep 5
echo ""
echo "✅ Service renamed successfully!"
echo ""
echo "Verifying service status..."
sudo systemctl status harvey-intelligence.service --no-pager | head -15

echo ""
echo "Testing Intelligence Engine..."
curl -s http://127.0.0.1:9000/ && echo "✅ Intelligence Engine responding"

echo ""
echo "Testing health endpoint..."
curl -s http://127.0.0.1:9000/api/internal/ml/health && echo ""

echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ RENAME COMPLETE"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Service management commands:"
echo "  sudo systemctl status harvey-intelligence.service"
echo "  sudo systemctl restart harvey-intelligence.service"
echo "  sudo journalctl -u harvey-intelligence.service -f"
echo ""
echo "Old ml-api.service has been removed."
echo "═══════════════════════════════════════════════════"
