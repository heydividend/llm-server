# 🚀 Deploy Harvey Using Replit's Git Interface

## Step 1: Open Git Panel in Replit

1. **Click the Tools icon** in the left sidebar
2. **Click the + button**
3. **Search for "Git"** and select it
4. The Git pane will open on the right side

## Step 2: Connect to GitHub

### If you haven't connected GitHub yet:
1. In the Git pane, click **"Connect to GitHub"**
2. Authorize Replit to access your GitHub account
3. Choose to create a **new repository** named `harvey-ai`

### If already connected:
1. Click **"Create a new repo on GitHub"** 
2. Name it: `harvey-ai` or `harvey-financial-advisor`
3. Make it **Private** (recommended for your API keys safety)

## Step 3: Prepare Files for Commit

### IMPORTANT: Protect Your Secrets!

Before committing, ensure `.gitignore` includes:
```
.env
*.log
__pycache__/
*.pyc
.pytest_cache/
logs/
tmp/
```

The `.env.example` file is safe to commit (it has placeholders, not real keys).

## Step 4: Commit and Push

In the Git pane:

1. **Review Changed Files** - You'll see all files listed
2. **Stage All Files** - Click "Stage all" button (or select individually)
3. **IMPORTANT**: Unstage `.env` if it appears (contains real secrets!)
4. **Write Commit Message**: 
   ```
   Initial Harvey deployment with ML service
   - Complete backend API with multi-model routing
   - ML prediction service with 8 endpoints
   - Frontend interface
   - Azure deployment configuration
   ```
5. **Click "Commit & push"**

## Step 5: Deploy on Azure VM

Now that your code is on GitHub, deployment is simple!

### SSH into your Azure VM:
```bash
ssh azureuser@20.81.210.213
```

### Clone your repository:
```bash
# Navigate to home directory
cd /home/azureuser

# Clone your private repo (GitHub will ask for authentication)
git clone https://github.com/YOUR_USERNAME/harvey-ai.git harvey

# If it's private, use personal access token:
git clone https://<token>@github.com/YOUR_USERNAME/harvey-ai.git harvey
```

### Set up the application:
```bash
# Enter directory
cd harvey

# Install Python dependencies
/home/azureuser/miniconda3/bin/pip install -r requirements.txt

# Create .env file with your secrets
cp .env.example .env
nano .env  # Add all your API keys here!

# Set up ODBC for database
cp odbc.ini ~/
cp odbcinst.ini ~/
export ODBCSYSINI=/home/azureuser

# Run deployment script
chmod +x deploy_harvey_azure.sh
./deploy_harvey_azure.sh
```

## Step 6: Configure Systemd Services

The deployment script handles this, but manually if needed:
```bash
# Create service files
sudo nano /etc/systemd/system/harvey-backend.service
```

Paste:
```ini
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
```

And for ML service:
```bash
sudo nano /etc/systemd/system/harvey-ml.service
```

Paste:
```ini
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
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable harvey-backend harvey-ml
sudo systemctl start harvey-backend harvey-ml
```

## Step 7: Verify Deployment

```bash
# Check services
sudo systemctl status harvey-backend
sudo systemctl status harvey-ml

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:9000/health

# View logs if needed
sudo journalctl -u harvey-backend -f
sudo journalctl -u harvey-ml -f
```

## 🔄 Future Updates Made Easy!

Once set up with Git, updates are super simple:

### In Replit:
1. Make your changes
2. Open Git pane
3. Stage changes
4. Commit with message
5. Push

### On Azure VM:
```bash
cd /home/azureuser/harvey
git pull origin main
sudo systemctl restart harvey-backend harvey-ml
```

## 🎯 GitHub Personal Access Token (If Needed)

If your repo is private, create a token:

1. Go to GitHub → Settings → Developer Settings
2. Personal Access Tokens → Tokens (classic)
3. Generate new token with `repo` scope
4. Use when cloning: `https://<token>@github.com/username/harvey-ai.git`

## ⚠️ Security Notes

- **NEVER commit `.env` with real keys**
- Keep repository **private** if it contains sensitive configuration
- Use GitHub Secrets for CI/CD (optional advanced setup)
- Always use `.env.example` with placeholder values

## 🚨 Troubleshooting

### Can't see Git pane?
- Make sure you're in the Tools section
- Try refreshing Replit page

### Push fails?
- Check GitHub connection in Replit settings
- Ensure you have write access to the repository

### Clone fails on Azure?
- Use personal access token for private repos
- Check your GitHub username is correct

## ✅ Success Checklist

- [ ] Git pane opened in Replit
- [ ] Connected to GitHub
- [ ] Created repository
- [ ] Committed code (without .env!)
- [ ] Pushed to GitHub
- [ ] Cloned on Azure VM
- [ ] Added real API keys to .env
- [ ] Services running on Azure
- [ ] Endpoints responding

Your Harvey deployment via Git is ready!