# Harvey Backend - Simplest Deployment Ever! (No SSH, No Uploads)

**Method:** Azure Portal Run Command  
**Time:** 5 minutes to edit, 10 minutes automated deployment  
**Requirements:** Just Azure Portal access

---

## 🎯 **What Makes This Simple?**

✅ **No SSH needed** - Use Azure Portal only  
✅ **No file uploads** - Script creates everything  
✅ **No downloads** - Everything runs in Azure  
✅ **Self-contained** - One script does it all  

---

## 🚀 **3-Step Deployment**

### **Step 1: Edit the Deployment Script** (5 minutes)

**File:** `deploy/AZURE_RUN_COMMAND_DEPLOY.sh` (in this Replit)

1. Download the script from Replit
2. Open in text editor
3. **Find this section** (around line 16):

```bash
# STEP 1: EDIT YOUR SECRETS HERE
HARVEY_AI_API_KEY="<YOUR_HARVEY_AI_API_KEY>"
SQLSERVER_HOST="<YOUR_SQLSERVER_HOST>"
SQLSERVER_DB="<YOUR_SQLSERVER_DB>"
SQLSERVER_USER="<YOUR_SQLSERVER_USER>"
SQLSERVER_PASSWORD="<YOUR_SQLSERVER_PASSWORD>"
OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
INTERNAL_ML_API_KEY="<YOUR_INTERNAL_ML_API_KEY>"
```

4. **Replace all `<YOUR_*>` with actual values** from Replit Secrets

**Example after editing:**
```bash
HARVEY_AI_API_KEY="hd_live_abc123xyz789"
SQLSERVER_HOST="your-server.database.windows.net"
SQLSERVER_DB="HeyDividend"
# ... etc
```

5. **Save the file**

---

### **Step 2: Run via Azure Portal** (2 minutes)

1. Go to **Azure Portal** (portal.azure.com)
2. Navigate to **Virtual Machines**
3. Click on your VM (the one at 20.81.210.213)
4. In the left menu, click **"Run command"** (under Operations)
5. Select **"RunShellScript"**
6. **Copy the ENTIRE edited script** and paste it into the text box
7. Click **"Run"**

**That's it!** Azure will execute the script on your VM.

---

### **Step 3: Wait for Completion** (10 minutes)

Azure will show you the script output in real-time. You'll see:

```
==========================================
Harvey Backend - Azure Run Command Deploy
==========================================

📦 Installing system dependencies...
✅ Dependencies installed

🔧 Configuring database drivers...
✅ Database drivers configured

📁 Creating Harvey backend directory...
✅ Harvey application files created

🐍 Creating Python virtual environment...
✅ Virtual environment created

... (continues)

==========================================
✅ Harvey Deployment Complete!
==========================================

Access Harvey at: http://20.81.210.213/
```

---

## ✅ **Verify Deployment**

Once the script completes, test Harvey:

**In your browser:**
```
http://20.81.210.213/
```

Should return:
```json
{
  "message": "Harvey AI Financial Advisor API",
  "version": "1.0",
  "status": "running"
}
```

**Test ML health:**
```
http://20.81.210.213/v1/ml/health
```

---

## 📋 **What Gets Deployed**

The script automatically:

1. ✅ Installs Python 3.11, FreeTDS, Nginx, all dependencies
2. ✅ Configures database drivers (FreeTDS + ODBC)
3. ✅ Creates Harvey directory structure
4. ✅ Creates minimal working FastAPI application
5. ✅ Creates `.env` file with your secrets
6. ✅ Sets up Python virtual environment
7. ✅ Installs all Python packages
8. ✅ Creates systemd services (Harvey + ML API)
9. ✅ Configures Nginx reverse proxy
10. ✅ Sets up UFW firewall
11. ✅ Starts all services
12. ✅ Runs health checks

**All automatically!**

---

## 🔧 **After Deployment - Add Full Harvey Code**

The deployment creates a **minimal working Harvey** with basic endpoints. To deploy your full Harvey application:

### **Option A: Clone from Git (Recommended)**

If you have Harvey in a Git repository:

1. Azure Portal → VM → **Run Command** → **RunShellScript**
2. Paste this:

```bash
cd /opt/harvey-backend
# Remove minimal files
rm -rf app/ main.py

# Clone your actual Harvey repository
git clone https://github.com/your-org/harvey-backend.git temp
mv temp/* temp/.* . 2>/dev/null || true
rm -rf temp

# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
systemctl restart harvey.service

echo "✅ Full Harvey deployed!"
```

### **Option B: Upload via Azure Portal**

1. Azure Portal → VM → **Connect** → **Bastion** (or SSH if you prefer)
2. Upload your Harvey code:
   ```bash
   cd /opt/harvey-backend
   # Upload files here
   ```
3. Restart service:
   ```bash
   sudo systemctl restart harvey.service
   ```

---

## 🆘 **Troubleshooting**

### **If script fails:**

Check the Run Command output for error messages. Common issues:

**"Permission denied"**
- The script runs as root, this shouldn't happen
- Check Azure VM permissions

**"Package not found"**
- Internet connectivity issue on VM
- Check Azure NSG allows outbound traffic

**"Service failed to start"**
- Check secrets are correct in .env
- View logs: `journalctl -u harvey.service -n 100`

### **Check service status:**

Azure Portal → VM → Run Command → RunShellScript:
```bash
systemctl status harvey.service
systemctl status nginx
journalctl -u harvey.service -n 50
```

### **View Harvey logs:**

```bash
tail -100 /var/log/harvey/error.log
tail -100 /var/log/nginx/harvey_error.log
```

---

## 🌐 **Azure NSG Configuration**

**Don't forget to configure Network Security Group!**

1. Azure Portal → VM → **Networking**
2. **Add inbound security rules:**
   - Port 22 (SSH) - Optional, for future access
   - Port 80 (HTTP) - **Required**
   - Port 443 (HTTPS) - **Required** (if using SSL)

---

## 🎉 **Success Checklist**

Deployment is successful when:

- ✅ Run Command script completes without errors
- ✅ `http://20.81.210.213/` returns Harvey API response
- ✅ `http://20.81.210.213/v1/ml/health` shows health status
- ✅ Azure NSG configured (ports 80/443 open)

---

## 📊 **What You Get**

After this deployment:

```
Azure VM (20.81.210.213)
├── Nginx (port 80/443) - Public facing
│   ├── Routes / → Harvey Backend (localhost:8000)
│   └── Routes /api/internal/ml/ → ML API (localhost:9000)
├── Harvey Backend (localhost:8000)
│   ├── FastAPI application
│   ├── Python 3.11 virtual environment
│   ├── All dependencies installed
│   └── Systemd service (auto-restart)
└── ML API (localhost:9000) - If already deployed
```

**Public URL:** `http://20.81.210.213/`

---

## 💡 **Pro Tips**

1. **Add SSL later:**
   ```bash
   # Via Run Command
   certbot --nginx -d your-domain.com
   ```

2. **Update Harvey code:**
   ```bash
   cd /opt/harvey-backend
   git pull origin main
   systemctl restart harvey.service
   ```

3. **View real-time logs:**
   ```bash
   journalctl -u harvey.service -f
   ```

4. **Check all services:**
   ```bash
   systemctl status harvey.service nginx
   ```

---

**That's it!** The simplest Harvey deployment ever - just edit secrets, paste script, and run! 🚀

No SSH, no file uploads, no complexity. Everything automated through Azure Portal's Run Command feature.
