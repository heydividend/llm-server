# Harvey Azure VM Deployment Guide

## 🚀 Quick Deployment

### Automatic Deployment
```bash
chmod +x deploy/deploy_to_azure.sh
./deploy/deploy_to_azure.sh
```

## 📋 Manual Deployment Steps

### Step 1: SSH into Azure VM
```bash
ssh azureuser@20.81.210.213
# Or with your key file:
ssh -i ~/.ssh/your-azure-key.pem azureuser@20.81.210.213
```

### Step 2: Navigate to Harvey Directory
```bash
cd /home/azureuser/harvey
```

### Step 3: Backup Current Deployment
```bash
# Create backup directory
mkdir -p ~/backups
cp -r ~/harvey ~/backups/harvey_$(date +%Y%m%d_%H%M%S)
```

### Step 4: Pull Latest Code
If using Git:
```bash
git pull origin main
```

If copying from Replit manually:
```bash
# From your local machine (Replit terminal):
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='logs' \
    ./ azureuser@20.81.210.213:/home/azureuser/harvey/
```

### Step 5: Install Dependencies
```bash
# On Azure VM
cd /home/azureuser/harvey
pip install -r requirements.txt
```

### Step 6: Update Environment Variables
```bash
# Edit .env file if needed
nano .env

# Ensure these are set:
AZURE_OPENAI_ENDPOINT=https://htmltojson-parser-openai-a1a8.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT_NAME=HarveyGPT-5
ML_API_BASE_URL=http://localhost:9000/api/internal/ml
```

### Step 7: Restart Harvey Services
```bash
# Stop services
sudo systemctl stop harvey-backend
sudo systemctl stop harvey-ml
sudo systemctl stop nginx

# Start services
sudo systemctl start harvey-backend
sudo systemctl start harvey-ml
sudo systemctl start nginx

# Check status
sudo systemctl status harvey-backend
sudo systemctl status harvey-ml
sudo systemctl status nginx
```

### Step 8: Verify Deployment
```bash
# Check backend health
curl http://localhost:8000/health
curl http://localhost:8000/v1/admin/status

# Check ML API
curl http://localhost:9000/api/internal/ml/health

# Check logs
sudo journalctl -u harvey-backend -f
sudo journalctl -u harvey-ml -f
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. FreeTDS/ODBC Driver Issues
```bash
# Install FreeTDS driver
sudo apt-get update
sudo apt-get install -y freetds-dev freetds-bin tdsodbc

# Configure ODBC
echo "[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" | sudo tee -a /etc/odbcinst.ini
```

#### 2. Port 8000 Not Accessible
```bash
# Check firewall rules
sudo ufw status
sudo ufw allow 8000/tcp
sudo ufw allow 9000/tcp

# Check Azure NSG (Network Security Group)
# Go to Azure Portal → VM → Networking → Add inbound port rule for 8000
```

#### 3. Service Won't Start
```bash
# Check logs
sudo journalctl -u harvey-backend -n 100
sudo journalctl -u harvey-ml -n 100

# Check Python path
which python
which pip

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

#### 4. Database Connection Issues
```bash
# Test SQL Server connection
python -c "import pyodbc; print(pyodbc.drivers())"

# Update connection string in .env
SQLSERVER_CONN_STR="Driver={FreeTDS};Server=your-server.database.windows.net;Database=harvey;UID=your-user;PWD=your-password;Port=1433;TDS_Version=8.0;"
```

## 🎯 Testing Production Endpoints

### From Local Machine
```bash
# Test backend
curl http://20.81.210.213:8000/health
curl http://20.81.210.213:8000/v1/admin/status

# Test Harvey Intelligence with new features
curl -X POST http://20.81.210.213:8000/v1/harvey/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a dividend aristocrat?"}'

# Test ML API
curl http://20.81.210.213:9000/api/internal/ml/health
```

## 📁 Service Files Location

- Backend service: `/etc/systemd/system/harvey-backend.service`
- ML API service: `/etc/systemd/system/harvey-ml.service`
- Nginx config: `/etc/nginx/sites-available/harvey`

## 🔄 Rollback Procedure

If deployment fails:
```bash
# Stop services
sudo systemctl stop harvey-backend
sudo systemctl stop harvey-ml

# Restore from backup
cd ~
rm -rf harvey
cp -r backups/harvey_[timestamp] harvey

# Restart services
sudo systemctl start harvey-backend
sudo systemctl start harvey-ml

# Verify rollback
curl http://localhost:8000/health
```

## 📊 Monitoring

### Check Service Logs
```bash
# Real-time logs
sudo journalctl -u harvey-backend -f
sudo journalctl -u harvey-ml -f

# Last 100 lines
sudo journalctl -u harvey-backend -n 100
sudo journalctl -u harvey-ml -n 100
```

### Check Resource Usage
```bash
htop
df -h
free -m
```

## ✅ Deployment Checklist

- [ ] Backup created
- [ ] Code updated
- [ ] Dependencies installed
- [ ] Environment variables verified
- [ ] Services restarted
- [ ] Health endpoints tested
- [ ] Harvey Intelligence endpoint tested
- [ ] Investment Explanation features verified
- [ ] Logs checked for errors
- [ ] External access verified (port 8000)