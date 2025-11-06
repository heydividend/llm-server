#!/bin/bash

# 🚀 Harvey Quick Deployment Script for Azure VM
# This script automates the entire deployment process

echo "================================================"
echo "🚀 Harvey Quick Deployment Starting..."
echo "================================================"

# Check if running on Azure VM
if [ "$USER" != "azureuser" ]; then
    echo "⚠️  Warning: This script is designed for Azure VM (azureuser)"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set deployment directory
DEPLOY_DIR="/home/azureuser/harvey"

# Create deployment directory
echo ""
echo "📂 Setting up deployment directory..."
if [ ! -d "$DEPLOY_DIR" ]; then
    mkdir -p $DEPLOY_DIR
fi

# Copy all files to deployment directory
echo "📦 Copying application files..."
cp -r * $DEPLOY_DIR/ 2>/dev/null || true

# Navigate to deployment directory
cd $DEPLOY_DIR

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."
/home/azureuser/miniconda3/bin/pip install -r requirements.txt

# Set up ODBC configuration
echo ""
echo "🔧 Configuring ODBC for SQL Server..."
cp odbc.ini ~/
cp odbcinst.ini ~/
export ODBCSYSINI=/home/azureuser

# Set up systemd services
echo ""
echo "⚙️  Installing systemd services..."
sudo cp systemd/harvey-backend.service /etc/systemd/system/
sudo cp systemd/harvey-ml.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable harvey-backend harvey-ml

# Create .env file if not exists
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "================================================"
    echo "⚠️  IMPORTANT: Edit .env file with your credentials!"
    echo "================================================"
    echo "Run: nano $DEPLOY_DIR/.env"
    echo ""
    echo "Add your keys:"
    echo "  - OPENAI_API_KEY"
    echo "  - AZURE_OPENAI_API_KEY"
    echo "  - GEMINI_API_KEY"
    echo "  - SQLSERVER_* database credentials"
    echo "  - Other API keys as needed"
    echo ""
    read -p "Press Enter after you've added your credentials..."
fi

# Start services
echo ""
echo "🎯 Starting Harvey services..."
sudo systemctl restart harvey-backend
sleep 2
sudo systemctl restart harvey-ml
sleep 2

# Check status
echo ""
echo "✅ Checking service status..."
sudo systemctl status harvey-backend --no-pager
echo ""
sudo systemctl status harvey-ml --no-pager

# Test endpoints
echo ""
echo "🧪 Testing endpoints..."
echo -n "Harvey API Health: "
curl -s http://localhost:8001/health | jq -r '.status' 2>/dev/null || echo "Failed"
echo -n "ML Service Health: "
curl -s http://localhost:9000/health | jq -r '.status' 2>/dev/null || echo "Failed"

# Display final information
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo "================================================"
echo "✅ Harvey Deployment Complete!"
echo "================================================"
echo ""
echo "📊 Service URLs:"
echo "  Harvey API: http://$PUBLIC_IP:8001"
echo "  ML Service: http://$PUBLIC_IP:9000"
echo ""
echo "🧪 Test commands:"
echo "  curl http://$PUBLIC_IP:8001/health"
echo "  curl http://$PUBLIC_IP:9000/health"
echo ""
echo "📝 View logs:"
echo "  sudo journalctl -u harvey-backend -f"
echo "  sudo journalctl -u harvey-ml -f"
echo ""
echo "🎨 Web Interface:"
echo "  Open frontend/harvey-test.html in a browser"
echo "  Update API URL to: http://$PUBLIC_IP:8001"
echo ""
echo "================================================"