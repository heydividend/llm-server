#!/bin/bash
# Harvey Git Deployment Setup for Azure VM
# Run this on your Azure VM to set up Git deployment

echo "============================================"
echo "Harvey Git Deployment Setup"
echo "============================================"

# Configuration
HARVEY_DIR="/home/azureuser/harvey"
REPO_URL="https://github.com/yourusername/harvey.git"  # Update this
BRANCH="main"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "1. Initializing Git repository..."
echo "============================================"

cd $HARVEY_DIR

# Initialize git if not already
if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✓ Git repository initialized${NC}"
else
    echo -e "${YELLOW}✓ Git repository already exists${NC}"
fi

# Create comprehensive .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
venv/
env/
ENV/

# Environment variables
.env
.env.local
.env.production
.env.development

# Logs
*.log
logs/
/var/log/
*.log.*

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# ML Models (if large)
*.pkl
*.h5
*.pt
*.pth
models/

# Secrets
secrets/
*.key
*.pem
*.cert

# Temporary files
tmp/
temp/
cache/

# Azure specific
.azure/
azureuser/
EOF

echo -e "${GREEN}✓ .gitignore created${NC}"

# Create deployment branch structure
echo ""
echo "2. Setting up deployment structure..."
echo "============================================"

# Create deployment info file
cat > DEPLOYMENT.md << 'EOF'
# Harvey Deployment Guide

## Quick Deploy to Azure VM

### 1. Clone Repository
```bash
git clone <your-repo-url> /home/azureuser/harvey
cd /home/azureuser/harvey
```

### 2. Set Environment Variables
```bash
cp .env.example .env
nano .env  # Add your secrets
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Services
```bash
sudo systemctl restart harvey-backend harvey-ml
```

## Service Configuration

- **Harvey API**: Port 8001
- **ML Service**: Port 9000
- **Database**: Azure SQL Server

## Monitoring

```bash
# Check status
sudo systemctl status harvey-backend harvey-ml

# View logs
sudo journalctl -u harvey-backend -f
sudo journalctl -u harvey-ml -f
```

## Updates

```bash
git pull origin main
sudo systemctl restart harvey-backend harvey-ml
```
EOF

echo -e "${GREEN}✓ Deployment documentation created${NC}"

# Create requirements.txt with all dependencies
echo ""
echo "3. Creating requirements file..."
echo "============================================"

cat > requirements.txt << 'EOF'
# Harvey Backend Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0
pyodbc==5.0.1
sqlalchemy==2.0.23
pandas==2.1.3
numpy==1.24.3
requests==2.31.0
httpx==0.25.2
aiofiles==23.2.1

# AI/ML Dependencies
openai==1.3.7
google-generativeai==0.3.0
tiktoken==0.5.1

# Web Scraping (for web search feature)
beautifulsoup4==4.12.2
lxml==4.9.3
trafilatura==1.6.2
readability-lxml==0.8.1
newspaper3k==0.2.8
markdown==3.5.1
py-markdown-table==0.3.3
mdformat==0.7.17

# Document Processing
azure-ai-documentintelligence==1.0.0
pypdf2==3.0.1
python-docx==1.1.0
openpyxl==3.1.2

# Additional utilities
python-multipart==0.0.6
typing-extensions==4.8.0
rich==13.7.0
EOF

echo -e "${GREEN}✓ requirements.txt created${NC}"

# Create systemd service templates
echo ""
echo "4. Creating systemd service templates..."
echo "============================================"

mkdir -p systemd

cat > systemd/harvey-backend.service << 'EOF'
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

cat > systemd/harvey-ml.service << 'EOF'
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

echo -e "${GREEN}✓ Systemd service templates created${NC}"

# Create deployment script
echo ""
echo "5. Creating automated deployment script..."
echo "============================================"

cat > deploy.sh << 'EOF'
#!/bin/bash
# Automated deployment script for Harvey

echo "Deploying Harvey updates..."

# Pull latest changes
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Copy systemd services if needed
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Restart services
sudo systemctl restart harvey-backend harvey-ml

# Check status
sudo systemctl status harvey-backend harvey-ml --no-pager

echo "Deployment complete!"
EOF

chmod +x deploy.sh
echo -e "${GREEN}✓ deploy.sh created${NC}"

# Create initial commit
echo ""
echo "6. Creating initial commit..."
echo "============================================"

git add -A
git commit -m "Initial Harvey deployment setup with ML service"

echo -e "${GREEN}✓ Initial commit created${NC}"

echo ""
echo "============================================"
echo "Git Deployment Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Create a GitHub/GitLab repository"
echo ""
echo "2. Add remote and push:"
echo "   git remote add origin YOUR_REPO_URL"
echo "   git push -u origin main"
echo ""
echo "3. On any update, just run:"
echo "   ./deploy.sh"
echo ""
echo "This will automatically:"
echo "- Pull latest changes"
echo "- Update dependencies"
echo "- Restart services"
echo ""