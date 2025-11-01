# Harvey Backend - Cloud-Init Deployment Guide

**Deployment Method:** Azure VM Custom Data (cloud-init)  
**Time Required:** 15 minutes (5 minutes manual, 10 minutes automated)  
**Difficulty:** Easy - Just upload files and apply cloud-init

---

## 📋 What is Cloud-Init?

Cloud-init is Azure's VM initialization system. You provide a YAML configuration, and Azure automatically runs it when the VM starts. Perfect for automated deployments!

---

## 🚀 Step-by-Step Deployment

### **Step 1: Prepare Harvey Code Package** (Already Done! ✅)

The deployment package is ready in Replit at: `/tmp/harvey-deployment/harvey-backend.tar.gz`

**Download it:**
1. In Replit file browser, go to `/tmp/harvey-deployment/`
2. Right-click `harvey-backend.tar.gz` → Download
3. Save it to your computer

---

### **Step 2: Edit Cloud-Init Script with Your Secrets** (5 minutes)

**File:** `deploy/cloud-init-harvey.yaml` (in this Replit)

**Download and edit:**
1. Download `cloud-init-harvey.yaml` from this Replit
2. Open in text editor
3. **Find this section** (around line 40):

```yaml
- path: /opt/harvey-backend/.env
  content: |
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
```

4. **Replace ALL `<YOUR_*>` with actual values** from Replit Secrets:
   - Get values from this Replit's Secrets (lock icon in left sidebar)
   - Copy each secret value and paste into the YAML file

**Example after editing:**
```yaml
- path: /opt/harvey-backend/.env
  content: |
    HARVEY_AI_API_KEY=hd_live_abc123xyz789
    SQLSERVER_HOST=your-server.database.windows.net
    SQLSERVER_DB=HeyDividend
    SQLSERVER_USER=sqladmin
    SQLSERVER_PASSWORD=YourActualPassword123!
    OPENAI_API_KEY=sk-proj-abc123xyz...
    ML_API_BASE_URL=http://127.0.0.1:9000/api/internal/ml
    INTERNAL_ML_API_KEY=hd_live_xyz789abc123
    ODBCSYSINI=/etc
    ENVIRONMENT=production
```

5. **Save the file**

---

### **Step 3: Upload Harvey Code to Azure VM** (2 minutes)

**Option A: Using Azure Portal Storage (Recommended)**

1. Go to Azure Portal → Storage Accounts → Create a temporary storage account (or use existing)
2. Create a container called `deployment`
3. Upload `harvey-backend.tar.gz` to the container
4. Get the blob URL

**Option B: Using SCP (If you can SSH)**

```bash
scp harvey-backend.tar.gz azureuser@20.81.210.213:/tmp/
```

**Option C: Direct Upload via VM (If SSH works)**

```bash
# SSH into VM
ssh azureuser@20.81.210.213

# Download from a URL (if you host it somewhere)
cd /tmp
wget https://your-storage-url/harvey-backend.tar.gz

# Or use Azure CLI to download from blob storage
az storage blob download \
  --account-name yourstorageaccount \
  --container-name deployment \
  --name harvey-backend.tar.gz \
  --file /tmp/harvey-backend.tar.gz
```

---

### **Step 4: Apply Cloud-Init to Azure VM** (2 minutes)

**Two methods to apply cloud-init:**

#### **Method A: Using Azure Portal Custom Data (For New VM or Redeployment)**

1. Azure Portal → Virtual Machines → Your VM
2. Click **"Redeploy"** (under Help section)
3. Or create a new VM and during creation:
   - Go to **"Advanced"** tab
   - Find **"Custom data"** field
   - Paste the **entire contents** of your edited `cloud-init-harvey.yaml`
4. Start/Restart the VM

#### **Method B: Using Azure CLI (Faster for Existing VM)**

```bash
# Save your edited cloud-init-harvey.yaml to a file
# Then run:

az vm run-command invoke \
  --resource-group <your-resource-group> \
  --name <your-vm-name> \
  --command-id RunShellScript \
  --scripts @cloud-init-harvey.yaml
```

#### **Method C: Manual Installation (If Cloud-Init Doesn't Work)**

If cloud-init isn't available, you can SSH and run the deployment script manually:

```bash
# SSH into VM
ssh azureuser@20.81.210.213

# Copy the deployment script from cloud-init YAML
# (Extract the deploy-harvey.sh content from the YAML)
# Save it to /tmp/deploy-harvey.sh

# Run it
sudo bash /tmp/deploy-harvey.sh
```

---

### **Step 5: Wait for Deployment to Complete** (10 minutes)

The VM will:
1. Install all packages (Python, FreeTDS, Nginx, etc.)
2. Configure FreeTDS and ODBC
3. Extract Harvey code
4. Create Python virtual environment
5. Install dependencies
6. Configure systemd services
7. Set up Nginx reverse proxy
8. Start all services
9. Run health checks

**Monitor progress:**

```bash
# SSH into VM and watch cloud-init logs
ssh azureuser@20.81.210.213
sudo tail -f /var/log/cloud-init-output.log
```

Or check the final message:
```bash
cat /var/run/cloud-init/result.json
```

---

### **Step 6: Verify Deployment** (2 minutes)

**From your browser:**
```
http://20.81.210.213/
```

Should show Harvey's welcome page!

**From command line:**
```bash
# Test Harvey
curl http://20.81.210.213/

# Test ML health
curl http://20.81.210.213/v1/ml/health

# Check service status
ssh azureuser@20.81.210.213
sudo systemctl status harvey.service
sudo systemctl status ml-api.service
sudo systemctl status nginx
```

---

## 🔧 Troubleshooting

### **If services fail to start:**

```bash
# SSH into VM
ssh azureuser@20.81.210.213

# Check Harvey logs
sudo journalctl -u harvey.service -n 100

# Check ML API logs
sudo journalctl -u ml-api.service -n 100

# Check cloud-init logs
sudo cat /var/log/cloud-init-output.log

# Check if .env file has secrets
cat /opt/harvey-backend/.env
```

### **Common Issues:**

**1. "harvey-backend.tar.gz not found"**
- Make sure you uploaded the tar.gz file to `/tmp/` on the VM
- The cloud-init script expects it at `/tmp/harvey-backend.tar.gz`

**2. "Database connection failed"**
- Check that secrets in `.env` are correct
- Verify Azure SQL firewall allows VM's public IP

**3. "Services not starting"**
- Check that ML API directory exists at `/home/azureuser/ml-api/`
- If ML API doesn't exist yet, comment out ml-api.service in cloud-init

**4. "Nginx test failed"**
- Check Nginx config: `sudo nginx -t`
- View Nginx errors: `sudo tail -100 /var/log/nginx/error.log`

---

## 🔄 Updating Harvey Code

To update Harvey after initial deployment:

```bash
# SSH into VM
ssh azureuser@20.81.210.213

# Upload new tar.gz to /tmp/
# Then:
cd /opt/harvey-backend
rm -rf app/ main.py requirements.txt  # Remove old code
tar -xzf /tmp/harvey-backend.tar.gz   # Extract new code
source venv/bin/activate
pip install -r requirements.txt        # Update dependencies

# Restart service
sudo systemctl restart harvey.service

# Check it started
sudo systemctl status harvey.service
```

---

## 🛡️ Azure NSG Configuration

**Don't forget to configure Network Security Group:**

1. Azure Portal → VM → Networking
2. Add inbound security rules:
   - Port 22 (SSH) - Source: Your IP (for security)
   - Port 80 (HTTP) - Source: Any
   - Port 443 (HTTPS) - Source: Any (if using SSL)
3. **Remove port 9000** - Should only be localhost

---

## 🎯 After Successful Deployment

1. **Set up SSL** (optional but recommended):
   ```bash
   ssh azureuser@20.81.210.213
   sudo certbot --nginx
   ```

2. **Update frontend** to point to new API URL:
   - Change from Replit URL to: `http://20.81.210.213`
   - Or your domain if you have one

3. **Keep Replit running** for 48 hours as backup

4. **Monitor logs** for any errors:
   ```bash
   sudo journalctl -u harvey.service -f
   ```

5. **Test all features:**
   - Chat API
   - Dividend queries
   - ML predictions
   - Alerts
   - Background services

---

## 📊 What Gets Deployed

After cloud-init completes, your VM will have:

```
/opt/harvey-backend/           # Harvey application
├── venv/                      # Python virtual environment
├── app/                       # Harvey code
├── main.py                    # FastAPI entry point
├── .env                       # Secrets (chmod 600)
└── requirements.txt

/etc/systemd/system/
├── harvey.service             # Harvey systemd service
└── ml-api.service            # ML API systemd service

/etc/nginx/sites-available/
└── harvey                     # Nginx reverse proxy config

/var/log/
├── harvey/                    # Harvey logs
├── ml-api/                    # ML API logs
└── nginx/                     # Nginx logs
```

---

## ✅ Success Criteria

Deployment is successful when:

- ✅ `curl http://20.81.210.213/` returns Harvey welcome page
- ✅ `curl http://20.81.210.213/v1/ml/health` shows ML health status
- ✅ `systemctl status harvey.service` shows "active (running)"
- ✅ `systemctl status ml-api.service` shows "active (running)"
- ✅ `systemctl status nginx` shows "active (running)"
- ✅ No errors in logs: `journalctl -u harvey.service -n 50`

---

**That's it!** Cloud-init automates the entire deployment. You just need to:
1. Edit cloud-init YAML with your secrets
2. Upload harvey-backend.tar.gz to VM
3. Apply cloud-init to VM
4. Wait 10 minutes
5. Harvey is live! 🎉
