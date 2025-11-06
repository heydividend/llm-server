#!/bin/bash

# Harvey Deployment Package Creator
# Creates a complete deployment package for Azure VM

echo "================================================"
echo "📦 Creating Harvey Deployment Package"
echo "================================================"

# Create deployment directory
DEPLOY_DIR="harvey-deployment"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

echo ""
echo "📂 Copying application files..."

# Copy main application files
cp main.py $DEPLOY_DIR/
cp requirements.txt $DEPLOY_DIR/
cp .env.example $DEPLOY_DIR/
cp -r app $DEPLOY_DIR/
cp -r ml_training $DEPLOY_DIR/
cp -r financial_models $DEPLOY_DIR/

# Copy configuration files
echo "⚙️ Copying configuration files..."
cp odbc.ini $DEPLOY_DIR/
cp odbcinst.ini $DEPLOY_DIR/

# Copy deployment scripts
echo "🚀 Copying deployment scripts..."
cp deploy_harvey_azure.sh $DEPLOY_DIR/

# Copy frontend files
echo "🎨 Copying frontend files..."
mkdir -p $DEPLOY_DIR/frontend
cp harvey-frontend-api.js $DEPLOY_DIR/frontend/
cp harvey-test.html $DEPLOY_DIR/frontend/

# Copy test files
echo "🧪 Copying test files..."
cp test_ml_integration.py $DEPLOY_DIR/
cp test_harvey_api.py $DEPLOY_DIR/

# Create systemd service files
echo "📋 Creating systemd service files..."
mkdir -p $DEPLOY_DIR/systemd

cat > $DEPLOY_DIR/systemd/harvey-backend.service << 'EOF'
[Unit]
Description=Harvey Backend API
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/harvey
Environment="ODBCSYSINI=/home/azureuser"
EnvironmentFile=/home/azureuser/harvey/.env
ExecStart=/home/azureuser/miniconda3/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > $DEPLOY_DIR/systemd/harvey-ml.service << 'EOF'
[Unit]
Description=Harvey ML Service
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/harvey/ml_training
Environment="ODBCSYSINI=/home/azureuser"
EnvironmentFile=/home/azureuser/harvey/.env
ExecStart=/home/azureuser/miniconda3/bin/python ml_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create quick deploy script
cat > $DEPLOY_DIR/quick_deploy.sh << 'EOF'
#!/bin/bash

# Quick deployment script for Harvey on Azure VM
echo "🚀 Harvey Quick Deployment Starting..."

# Check if running on Azure VM
if [ "$USER" != "azureuser" ]; then
    echo "Warning: This script is designed for Azure VM (azureuser)"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
/home/azureuser/miniconda3/bin/pip install -r requirements.txt

# Set up ODBC configuration
echo "🔧 Configuring ODBC..."
cp odbc.ini ~/
cp odbcinst.ini ~/

# Set up systemd services
echo "⚙️ Installing systemd services..."
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable harvey-backend harvey-ml

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️ IMPORTANT: Edit .env file with your actual credentials!"
    echo "Run: nano .env"
    echo ""
fi

# Start services
echo "🎯 Starting Harvey services..."
sudo systemctl restart harvey-backend harvey-ml

# Check status
echo ""
echo "✅ Deployment complete! Checking status..."
sudo systemctl status harvey-backend harvey-ml --no-pager

echo ""
echo "================================================"
echo "Harvey is deployed!"
echo ""
echo "API: http://$(hostname -I | awk '{print $1}'):8001"
echo "ML:  http://$(hostname -I | awk '{print $1}'):9000"
echo ""
echo "Test with:"
echo "curl http://localhost:8001/health"
echo "curl http://localhost:9000/health"
echo "================================================"
EOF

chmod +x $DEPLOY_DIR/quick_deploy.sh

# Create deployment instructions
cat > $DEPLOY_DIR/DEPLOY_README.md << 'EOF'
# 🚀 Harvey Deployment Instructions

## Quick Start

### Step 1: Transfer to Azure VM
From your local machine:
```bash
# Transfer the entire deployment folder
scp -r harvey-deployment azureuser@20.81.210.213:~/
```

### Step 2: Deploy on Azure VM
```bash
# SSH into Azure VM
ssh azureuser@20.81.210.213

# Navigate to deployment directory
cd harvey-deployment

# Run quick deploy
./quick_deploy.sh
```

### Step 3: Configure Secrets
Edit the `.env` file with your actual API keys:
```bash
nano .env
```

Add your keys:
- OPENAI_API_KEY
- AZURE_OPENAI_API_KEY
- GEMINI_API_KEY
- Database credentials
- etc.

### Step 4: Restart Services
```bash
sudo systemctl restart harvey-backend harvey-ml
```

## Manual Deployment Steps

If you prefer manual control:

### 1. Copy files to final location
```bash
sudo mkdir -p /home/azureuser/harvey
sudo cp -r * /home/azureuser/harvey/
sudo chown -R azureuser:azureuser /home/azureuser/harvey
```

### 2. Install dependencies
```bash
cd /home/azureuser/harvey
/home/azureuser/miniconda3/bin/pip install -r requirements.txt
```

### 3. Configure ODBC
```bash
cp odbc.ini ~/
cp odbcinst.ini ~/
```

### 4. Install services
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable harvey-backend harvey-ml
```

### 5. Start services
```bash
sudo systemctl start harvey-backend harvey-ml
```

## Testing

### Health checks
```bash
curl http://localhost:8001/health
curl http://localhost:9000/health
```

### Test chat
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AAPL dividend yield?"}'
```

### Test ML predictions
```bash
python test_ml_integration.py
```

## Troubleshooting

### View logs
```bash
sudo journalctl -u harvey-backend -f
sudo journalctl -u harvey-ml -f
```

### Restart services
```bash
sudo systemctl restart harvey-backend harvey-ml
```

### Check ports
```bash
sudo netstat -tlnp | grep -E '8001|9000'
```

## Frontend Access

The web interface is in the `frontend/` folder:
- Open `harvey-test.html` in a browser
- Update the API URL if needed
EOF

echo ""
echo "✅ Deployment package created in: $DEPLOY_DIR/"
echo ""
echo "📊 Package contents:"
ls -la $DEPLOY_DIR/
echo ""
echo "📦 Total size:"
du -sh $DEPLOY_DIR/
echo ""
echo "Next steps:"
echo "1. Download the 'harvey-deployment' folder"
echo "2. Transfer to Azure VM: scp -r harvey-deployment azureuser@20.81.210.213:~/"
echo "3. SSH to VM and run: cd harvey-deployment && ./quick_deploy.sh"
echo ""