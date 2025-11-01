# Harvey - Push to Git Repository Guide

## ✅ Repository is Ready to Push!

The codebase has been cleaned up and prepared for Git. Here's how to push it:

---

## 🚀 Quick Push to GitHub (Recommended)

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `harvey-backend` (or your preferred name)
3. Description: "Harvey - AI Financial Advisor with ML-powered dividend analysis"
4. **Important:** Choose **Private** (contains deployment scripts)
5. **Do NOT** initialize with README (we already have one)
6. Click **Create repository**

### Step 2: Push from Replit

Run these commands in the Replit shell:

```bash
# Set your GitHub username and repo name
GITHUB_USER="your-github-username"
REPO_NAME="harvey-backend"

# Add GitHub as remote (use HTTPS for simplicity)
git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git

# Verify remote is set
git remote -v

# Add all files
git add .

# Commit
git commit -m "Initial commit: Harvey AI backend with portfolio upload, feedback system, and ML integration"

# Push to GitHub
git push -u origin main
```

**Authentication:** GitHub will prompt for your username and **Personal Access Token** (not password).

---

## 🔑 GitHub Personal Access Token Setup

If you don't have a token:

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name: `Replit Harvey Deployment`
4. Expiration: 90 days (or your preference)
5. Scopes: Check **`repo`** (full control of private repositories)
6. Click **Generate token**
7. **Copy the token** (you won't see it again!)
8. Use this token as your password when pushing

---

## 🔄 Alternative: Push to GitLab/Bitbucket

### GitLab:
```bash
git remote add origin https://gitlab.com/your-username/harvey-backend.git
git push -u origin main
```

### Bitbucket:
```bash
git remote add origin https://bitbucket.org/your-username/harvey-backend.git
git push -u origin main
```

---

## 📋 What's Being Pushed?

### ✅ Included:
- All source code (`app/`, `main.py`)
- Deployment scripts (`deploy/`)
- Documentation (all .md files)
- Requirements (`requirements.txt`)
- Static files (`static/`)
- Configuration (`.replit`, `.gitignore`)

### ❌ Excluded (via .gitignore):
- Environment files (`.env`) - NEVER commit secrets!
- Logs (`logs/`, `*.log`)
- Python cache (`__pycache__/`)
- Temporary files
- Replit-specific runtime files
- Large data files

---

## 🔒 Security Checklist

Before pushing, verify:

- [ ] `.env` is in `.gitignore` ✅ (confirmed)
- [ ] `.env.example` has no real secrets ✅ (confirmed)
- [ ] Deployment scripts use placeholders ✅ (confirmed)
- [ ] No API keys in code ✅ (environment variables only)

---

## 📝 After Pushing

Once pushed to GitHub:

### 1. Update Azure VM Deployment Script

Edit `deploy/AZURE_RUN_COMMAND_DEPLOY.sh` to pull from your GitHub:

```bash
# Change this line (around line 76):
# FROM:
git clone https://example.com/harvey-backend.git /opt/harvey-backend

# TO:
git clone https://github.com/YOUR_USERNAME/harvey-backend.git /opt/harvey-backend
```

### 2. Deploy to Azure VM

Use the updated deployment script:
```
Azure Portal → Your VM → Run Command → Paste updated script → Run
```

### 3. Enable Auto-Updates (Optional)

Add this to your VM crontab for automatic updates:
```bash
# SSH into Azure VM
ssh azureuser@20.81.210.213

# Edit crontab
crontab -e

# Add this line (updates daily at 3 AM):
0 3 * * * cd /opt/harvey-backend && git pull && systemctl restart harvey-backend
```

---

## 🔄 Future Updates

After making changes in Replit:

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add new feature: XYZ"

# Push to GitHub
git push origin main

# Then deploy to Azure VM
# Option 1: SSH and pull
ssh azureuser@20.81.210.213
cd /opt/harvey-backend
sudo git pull
sudo systemctl restart harvey-backend

# Option 2: Re-run deployment script via Azure Portal
```

---

## 🛠️ Troubleshooting

### "Repository not found"
- Check repository name and username are correct
- Verify repository is public OR you're using correct credentials

### "Authentication failed"
- Use Personal Access Token, not password
- Token must have `repo` scope
- Token hasn't expired

### "Remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/your-username/harvey-backend.git
```

### "Large files rejected"
```bash
# Remove large files from git
git rm --cached path/to/large/file
echo "path/to/large/file" >> .gitignore
git commit --amend
git push -f origin main
```

---

## 📚 Repository Structure

```
harvey-backend/
├── app/                      # Main application code
│   ├── controllers/          # Request handlers
│   ├── routes/               # API routes
│   ├── services/             # Business logic
│   ├── core/                 # Core utilities
│   └── database/             # Database schemas
├── deploy/                   # Deployment scripts
├── static/                   # Static web files
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
└── *.md                      # Documentation
```

---

## ✅ Ready to Push!

Your repository is now ready. Follow Step 1 and Step 2 above to push to GitHub.

After pushing, you'll be able to:
- Deploy latest code to Azure VM easily
- Track changes and version history
- Collaborate with others
- Automate deployments via GitHub Actions (future)

**Next:** Create your GitHub repository and run the push commands!
