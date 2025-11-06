# 🚀 Harvey Deployment Package - Complete Instructions

## 📦 What's Included

This deployment package contains everything needed to deploy Harvey on your Azure VM:
- ✅ Complete Harvey backend (main.py + app/)
- ✅ ML Service (ml_training/)
- ✅ Financial models
- ✅ Frontend interface (harvey-test.html)
- ✅ All dependencies (requirements.txt)
- ✅ Systemd service files
- ✅ ODBC configuration for SQL Server
- ✅ Quick deployment script

## 🔄 Option 1: Quick Deployment (Recommended)

### Step 1: Download Deployment Package
In Replit, download the entire `harvey-deployment` folder

### Step 2: Transfer to Azure VM
From your local machine (Mac):
```bash
# Transfer the deployment package
scp -r harvey-deployment azureuser@20.81.210.213:~/
```

### Step 3: Deploy on Azure VM
```bash
# SSH into your Azure VM
ssh azureuser@20.81.210.213

# Navigate to deployment folder
cd harvey-deployment

# Make deployment script executable
chmod +x quick_deploy.sh

# Run deployment (handles everything!)
./quick_deploy.sh
```

### Step 4: Configure API Keys
When prompted, edit the .env file:
```bash
nano /home/azureuser/harvey/.env
```

Add your actual API keys:
```
# OpenAI
OPENAI_API_KEY=your_openai_key_here

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment

# Google Gemini
GEMINI_API_KEY=your_gemini_key

# Database (already configured)
SQLSERVER_HOST=hey-dividend-sql-server.database.windows.net
SQLSERVER_USER=your_db_user
SQLSERVER_PASSWORD=your_db_password
SQLSERVER_DB=your_db_name

# Other keys...
```

## 🔧 Manual Deployment (If Preferred)

### Step 1: Copy Files
```bash
# Create Harvey directory
sudo mkdir -p /home/azureuser/harvey

# Copy all files
sudo cp -r harvey-deployment/* /home/azureuser/harvey/

# Set permissions
sudo chown -R azureuser:azureuser /home/azureuser/harvey
```

### Step 2: Install Dependencies
```bash
cd /home/azureuser/harvey
/home/azureuser/miniconda3/bin/pip install -r requirements.txt
```

### Step 3: Configure ODBC
```bash
cp odbc.ini ~/
cp odbcinst.ini ~/
export ODBCSYSINI=/home/azureuser
```

### Step 4: Set Up Services
```bash
# Install systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable harvey-backend harvey-ml
```

### Step 5: Configure Environment
```bash
cp .env.example .env
nano .env  # Add your API keys
```

### Step 6: Start Services
```bash
sudo systemctl start harvey-backend
sudo systemctl start harvey-ml
```

## ✅ Verification

### Check Services Running
```bash
sudo systemctl status harvey-backend
sudo systemctl status harvey-ml
```

### Test Endpoints
```bash
# Test Harvey API
curl http://localhost:8001/health

# Test ML Service
curl http://localhost:9000/health

# Test chat functionality
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AAPL dividend yield?"}'
```

### Run Integration Tests
```bash
cd /home/azureuser/harvey
python test_ml_integration.py
python test_harvey_api.py
```

## 🌐 Azure Portal Configuration

### Required Ports (Network Security Group)
1. Go to Azure Portal → Your VM → Networking
2. Add inbound security rules:
   - **Port 8001**: Harvey API (Priority 100)
   - **Port 9000**: ML Service (Priority 110)

## 🎨 Accessing the Web Interface

### From Your Local Machine
1. Open `frontend/harvey-test.html` in a browser
2. Update the API URL to: `http://20.81.210.213:8001`
3. Start chatting with Harvey!

### Or Host on Azure VM
```bash
# Copy frontend to web directory
sudo cp frontend/* /var/www/html/
```

## 🔍 Monitoring & Troubleshooting

### View Logs
```bash
# Harvey API logs
sudo journalctl -u harvey-backend -f

# ML Service logs
sudo journalctl -u harvey-ml -f

# Last 100 lines
sudo journalctl -u harvey-backend -n 100
```

### Restart Services
```bash
sudo systemctl restart harvey-backend harvey-ml
```

### Check Ports
```bash
sudo netstat -tlnp | grep -E '8001|9000'
```

### Test Database Connection
```bash
python -c "import pyodbc; print('Database OK')"
```

## 📊 Service Architecture

```
User Browser
     ↓
Frontend (harvey-test.html)
     ↓
Harvey API (:8001)
     ↓
ML Service (:9000)
     ↓
Azure SQL Database
```

## 🚨 Common Issues & Solutions

### Issue: Services not starting
```bash
# Check Python path
which python
# Should be: /home/azureuser/miniconda3/bin/python

# Fix if needed
export PATH="/home/azureuser/miniconda3/bin:$PATH"
```

### Issue: Database connection fails
```bash
# Check ODBC configuration
odbcinst -q -d
# Should show: [ODBC Driver 18 for SQL Server]

# Test connection
isql -v harvey-db
```

### Issue: Port already in use
```bash
# Find process using port
sudo lsof -i :8001

# Kill if needed
sudo kill -9 <PID>
```

## 🔄 Updating Harvey

### Quick Update Process
```bash
# Transfer updated files
scp -r harvey-deployment azureuser@20.81.210.213:~/

# On Azure VM
cd ~/harvey-deployment
./quick_deploy.sh
```

### Or Manual Update
```bash
# Copy new files
cp -r ~/harvey-deployment/* /home/azureuser/harvey/

# Restart services
sudo systemctl restart harvey-backend harvey-ml
```

## ✨ Features Enabled

With this deployment, you get:
- ✅ Multi-model AI routing (GPT-5, Grok-4, DeepSeek-R1, Gemini, FinGPT)
- ✅ ML predictions (growth rates, risk scores, clustering)
- ✅ Dividend analysis and portfolio optimization
- ✅ Web search integration
- ✅ Document processing (PDF, Excel, CSV)
- ✅ Beautiful web interface
- ✅ Real-time streaming responses
- ✅ Investment explanations
- ✅ Financial models integration

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Verify all API keys are set correctly
3. Ensure ports are open in Azure NSG
4. Test each component individually

Your Harvey system should be fully operational after following these steps!