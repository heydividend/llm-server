# Harvey Backend - Azure Deployment Instructions

## 🎯 Latest Code Pushed to GitHub

Your code is now at: **https://github.com/heydividend/llm-server**

Commit: `90e43f2` - Portfolio upload, PDF processing, feedback system

---

## 🚀 Deploy to Azure VM (20.81.210.213)

Choose the method that works best for you:

---

### **Method 1: Azure Portal Run Command** ⭐ (Easiest - No SSH Required)

1. **Edit the Deployment Script**
   - Open: `deploy/AZURE_RUN_COMMAND_DEPLOY.sh`
   - **Line 27:** Add your OpenAI API key: `OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE`
   - Save the file

2. **Run in Azure Portal**
   - Go to: https://portal.azure.com
   - Navigate to your VM (20.81.210.213)
   - Click: **Run command** → **RunShellScript**
   - **Copy the entire `AZURE_RUN_COMMAND_DEPLOY.sh` script** and paste it
   - Click **Run**
   - Wait 5-10 minutes for full deployment

3. **Verify Deployment**
   - Check output shows: "✅ Harvey Deployment Complete!"
   - Service status shows: "✅ Harvey Backend: Running"
   - Access Harvey at: http://20.81.210.213/
   
**What This Does:**
- ✅ Clones full Harvey repository from GitHub
- ✅ Installs all dependencies from requirements.txt
- ✅ Configures database drivers for Azure SQL Server  
- ✅ Sets up systemd services and Nginx reverse proxy
- ✅ Deploys complete Harvey with all features (portfolio upload, PDF processing, feedback system, ML predictions, alert suggestions)

---

### **Method 2: SSH from Your Local Machine** (Requires SSH Access)

```bash
# Connect to Azure VM
ssh azureuser@20.81.210.213

# Pull latest code
cd /opt/harvey-backend
sudo git pull origin main

# Update dependencies
sudo /opt/harvey-backend/venv/bin/pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart harvey-backend

# Verify it's running
sudo systemctl status harvey-backend
curl http://localhost:8000/healthz

# Check logs
sudo journalctl -u harvey-backend -f
```

---

### **Method 3: Automated Git Pull** (Set It and Forget It)

Set up automatic updates from GitHub:

```bash
# SSH into Azure VM
ssh azureuser@20.81.210.213

# Create update script
sudo tee /usr/local/bin/update-harvey.sh > /dev/null << 'EOF'
#!/bin/bash
cd /opt/harvey-backend
git pull origin main
/opt/harvey-backend/venv/bin/pip install -r requirements.txt --upgrade
systemctl restart harvey-backend
EOF

sudo chmod +x /usr/local/bin/update-harvey.sh

# Add to crontab (runs daily at 3 AM)
echo "0 3 * * * root /usr/local/bin/update-harvey.sh >> /var/log/harvey-update.log 2>&1" | sudo tee -a /etc/crontab
```

---

## 📊 Deploy Feedback Database Schema

After deploying the backend, create the feedback tables in Azure SQL Server:

### **Method A: Azure Portal Query Editor**

1. Go to: **Azure Portal** → **SQL Databases** → **HeyDividend**
2. Click: **Query editor**
3. Login with SQL credentials
4. Open file: `app/database/feedback_schema.sql`
5. **Copy entire contents** and paste into query editor
6. Click **Run**

### **Method B: SQL Server Management Studio (SSMS)**

1. Connect to: `your-server.database.windows.net`
2. Open: `app/database/feedback_schema.sql`
3. Execute the script
4. Verify 4 new tables were created:
   - `conversation_feedback`
   - `successful_response_patterns`
   - `user_preferences`
   - `training_data_export`

---

## ✅ Verify Deployment

Test the new features:

```bash
# Test portfolio upload
curl -X POST http://20.81.210.213/v1/chat/completions \
  -H "Authorization: Bearer YOUR_HARVEY_API_KEY" \
  -F 'messages=[{"role":"user","content":"Analyze my portfolio"}]' \
  -F "file=@test_portfolio.csv"

# Test PDF.co health
curl http://20.81.210.213/v1/pdfco/health

# Expected: {"status":"healthy","pdfco_configured":true,...}

# Test feedback analytics
curl -H "Authorization: Bearer YOUR_HARVEY_API_KEY" \
  http://20.81.210.213/v1/feedback/analytics

# Test basic health
curl http://20.81.210.213/healthz
```

---

## 🔧 Troubleshooting

### Deployment Failed

```bash
# Check service status
sudo systemctl status harvey-backend

# View logs
sudo journalctl -u harvey-backend -n 100

# Restart service
sudo systemctl restart harvey-backend
```

### Database Connection Issues

Check `/opt/harvey-backend/.env` has correct values:
- `SQLSERVER_HOST`
- `SQLSERVER_DB`
- `SQLSERVER_USER`
- `SQLSERVER_PASSWORD`

### PDF.co Not Working

Add `PDFCO_API_KEY` to `/opt/harvey-backend/.env`

### ML API Not Responding

The ML API is not deployed yet. To deploy:
1. Follow: `deploy/ML_API_DEPLOYMENT.md`
2. Or set `ML_API_BASE_URL=http://localhost:9000/api/internal/ml`

---

## 📋 What Got Deployed

✅ **New Features:**
- Multi-format portfolio upload (CSV, Excel, PDF, screenshots)
- PDF.co integration for document processing
- Feedback-driven learning system
- GPT-4o fine-tuning pipeline
- ML API timeout optimizations (5s)

✅ **Infrastructure:**
- Updated deployment scripts
- Database schemas for feedback system
- Performance improvements

✅ **Documentation:**
- Complete API guides
- Deployment instructions
- Feature capabilities

---

## 🎯 Next Steps

1. **Deploy using Method 1** (Azure Portal - easiest)
2. **Create feedback database tables** (run feedback_schema.sql)
3. **Test new features** (portfolio upload, PDF.co)
4. **Monitor logs** for any issues

---

## 📞 Support

- **View logs:** `sudo journalctl -u harvey-backend -f`
- **Restart service:** `sudo systemctl restart harvey-backend`
- **Check status:** `sudo systemctl status harvey-backend`
- **Test health:** `curl http://localhost:8000/healthz`

---

**Ready to deploy!** Use Method 1 (Azure Portal) for the easiest deployment.
