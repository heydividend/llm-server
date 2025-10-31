# Harvey Backend - Quick Deployment to Azure VM

**Time Required:** 15 minutes  
**Manual Steps:** Just 3 commands!

---

## 🚀 Super Simple Deployment

All the hard work is done. You just need to:

### **Step 1: Download files from Replit** (1 minute)

In this Replit, the deployment package is ready at `/tmp/harvey-deployment/`

**Download these files to your computer:**
- `harvey-backend.tar.gz` (11 MB - all your Harvey code)
- Use Replit's file browser: Click `/tmp/harvey-deployment/` → Right-click files → Download

---

### **Step 2: Upload to Azure VM** (2 minutes)

On your local computer, open terminal and run:

```bash
# Upload deployment package to Azure VM
scp harvey-backend.tar.gz azureuser@20.81.210.213:/tmp/
```

You can also copy the automation scripts from `/home/runner/workspace/deploy/` in Replit:
- `setup_azure_vm.sh`
- `deploy_harvey.sh`

Or I can recreate them on Azure VM (they're small).

---

### **Step 3: Run deployment on Azure VM** (10 minutes - automated)

SSH into your Azure VM:

```bash
ssh azureuser@20.81.210.213
```

Then run this **single command block** (copy-paste everything):

```bash
# Create deployment scripts on Azure VM
cat > /tmp/setup_azure_vm.sh <<'SCRIPT1'
#!/bin/bash
set -e
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip freetds-dev freetds-bin unixodbc unixodbc-dev nginx certbot python3-certbot-nginx git htop curl wget

echo "🔧 Configuring FreeTDS..."
sudo tee /etc/freetds/freetds.conf > /dev/null <<EOF
[global]
tds version = 7.4
client charset = UTF-8
EOF

echo "🔧 Configuring ODBC..."
sudo tee /etc/odbcinst.ini > /dev/null <<EOF
[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
EOF

echo "📁 Creating directories..."
sudo mkdir -p /opt/harvey-backend /var/log/harvey /var/log/ml-api
sudo chown $USER:$USER /opt/harvey-backend /var/log/harvey /var/log/ml-api

echo "🔥 Configuring firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw delete allow 9000/tcp 2>/dev/null || true

echo "✅ System setup complete!"
SCRIPT1

# Make it executable and run it
chmod +x /tmp/setup_azure_vm.sh
/tmp/setup_azure_vm.sh

# Extract Harvey code
cd /opt/harvey-backend
tar -xzf /tmp/harvey-backend.tar.gz

# Create .env file with your secrets
# ⚠️ IMPORTANT: Replace <YOUR_*> with actual values from Replit Secrets!
cat > .env <<'ENV'
HARVEY_AI_API_KEY=<YOUR_HARVEY_AI_API_KEY>
SQLSERVER_HOST=<YOUR_SQLSERVER_HOST>
SQLSERVER_DB=<YOUR_SQLSERVER_DB>
SQLSERVER_USER=<YOUR_SQLSERVER_USER>
SQLSERVER_PASSWORD=<YOUR_SQLSERVER_PASSWORD>
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
ML_API_BASE_URL=http://127.0.0.1:9000/api/internal/ml
INTERNAL_ML_API_KEY=<YOUR_INTERNAL_ML_API_KEY>
ODBCSYSINI=/etc
ENVIRONMENT=production
ENV

# ⚠️ STOP HERE - Edit .env file with your actual secrets!
echo ""
echo "⚠️  IMPORTANT: Edit /opt/harvey-backend/.env with your actual secrets"
echo "Run: nano /opt/harvey-backend/.env"
echo ""
echo "After editing .env, run the deployment script:"
echo "bash /tmp/deploy_harvey.sh"
```

### **Step 4: Edit .env with your secrets** (2 minutes)

```bash
nano /opt/harvey-backend/.env
```

Replace all `<YOUR_*>` placeholders with actual values from your Replit Secrets.

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

---

### **Step 5: Complete deployment** (5 minutes - automated)

Run this **single command** to finish deployment:

```bash
cat > /tmp/deploy_harvey.sh <<'SCRIPT2'
#!/bin/bash
set -e
cd /opt/harvey-backend

echo "🐍 Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

chmod 600 .env

echo "🔍 Testing database..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
import pyodbc
conn_str = f\"DRIVER={{FreeTDS}};SERVER={os.getenv('SQLSERVER_HOST')};DATABASE={os.getenv('SQLSERVER_DB')};UID={os.getenv('SQLSERVER_USER')};PWD={os.getenv('SQLSERVER_PASSWORD')};TDS_Version=7.4;Port=1433;\"
try:
    conn = pyodbc.connect(conn_str, timeout=10)
    print('✅ Database OK!')
    conn.close()
except Exception as e:
    print(f'❌ Database failed: {e}')
    exit(1)
"

echo "🔧 Creating systemd services..."
sudo tee /etc/systemd/system/harvey.service > /dev/null <<EOF
[Unit]
Description=Harvey AI Financial Advisor Backend
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/harvey-backend
Environment="PATH=/opt/harvey-backend/venv/bin"
Environment="ODBCSYSINI=/etc"
ExecStart=/opt/harvey-backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=append:/var/log/harvey/access.log
StandardError=append:/var/log/harvey/error.log

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/ml-api.service > /dev/null <<EOF
[Unit]
Description=Harvey ML Prediction API
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/home/$USER/ml-api
Environment="PATH=/home/$USER/ml-api/venv/bin"
ExecStart=/home/$USER/ml-api/venv/bin/uvicorn main:app --host 127.0.0.1 --port 9000 --workers 2
Restart=always
RestartSec=10
StandardOutput=append:/var/log/ml-api/access.log
StandardError=append:/var/log/ml-api/error.log

[Install]
WantedBy=multi-user.target
EOF

echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/harvey > /dev/null <<'EOF'
upstream harvey_backend { server 127.0.0.1:8000; }
upstream ml_api { server 127.0.0.1:9000; }

server {
    listen 80;
    server_name _;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;

    location / {
        proxy_pass http://harvey_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
    }

    location /api/internal/ml/ {
        proxy_pass http://ml_api;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    client_max_body_size 50M;
    access_log /var/log/nginx/harvey_access.log;
    error_log /var/log/nginx/harvey_error.log;
}
EOF

sudo ln -sf /etc/nginx/sites-available/harvey /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable harvey.service ml-api.service
sudo systemctl restart harvey.service ml-api.service nginx
sleep 5

echo "🔍 Health checks..."
curl -s http://127.0.0.1:8000/ > /dev/null && echo "✅ Harvey OK" || echo "❌ Harvey failed"
curl -s http://127.0.0.1:9000/health > /dev/null && echo "✅ ML API OK" || echo "❌ ML API failed"
curl -s http://127.0.0.1/ > /dev/null && echo "✅ Nginx OK" || echo "❌ Nginx failed"

echo ""
echo "🎉 Deployment complete!"
echo "Harvey: http://$(curl -s ifconfig.me)/"
echo ""
echo "Commands:"
echo "  Logs: sudo journalctl -u harvey.service -f"
echo "  Restart: sudo systemctl restart harvey.service"
SCRIPT2

chmod +x /tmp/deploy_harvey.sh
bash /tmp/deploy_harvey.sh
```

---

## ✅ **Done! Harvey is Live!**

After the script completes, Harvey will be running at:

**http://20.81.210.213/**

### **Verify it works:**

```bash
# Test from Azure VM
curl http://20.81.210.213/

# Test ML health
curl http://20.81.210.213/v1/ml/health

# View logs
sudo journalctl -u harvey.service -f
```

---

## 📋 **Don't Forget:**

1. **Azure NSG Configuration:**
   - Go to Azure Portal → VM → Networking
   - Add inbound rules for ports 80 and 443
   - Remove port 9000 (only localhost access needed)

2. **Optional - Add SSL:**
   ```bash
   sudo certbot --nginx
   ```

3. **Keep Replit running** for 48 hours as backup while you test Azure VM

---

## 🆘 **If Something Goes Wrong:**

```bash
# Check service status
sudo systemctl status harvey.service
sudo systemctl status ml-api.service

# View logs
sudo journalctl -u harvey.service -n 100
sudo journalctl -u ml-api.service -n 100

# Restart services
sudo systemctl restart harvey.service
sudo systemctl restart ml-api.service
```

---

## 📊 **After Deployment:**

Your architecture will be:

```
Internet → Azure NSG (ports 80/443) → Nginx → Harvey (8000)
                                            → ML API (9000)
```

Both services running on localhost, only accessible via Nginx reverse proxy!

**Cost Savings:** ~$20-40/month (no more Replit hosting fees!)
**Performance:** ML predictions via localhost (much faster!)
**Security:** Only Nginx exposed, services protected on localhost

---

**That's it!** Your Harvey backend will be fully deployed on Azure VM with just these simple steps! 🚀
