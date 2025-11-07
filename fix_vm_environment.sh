#!/bin/bash

echo "Starting Azure VM environment fix..."
cd /home/azureuser/harvey

# 1. Fix environment variables loading
echo "=================================================="
echo "1. Setting up environment variables..."
echo "=================================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    touch .env
fi

# Source the environment from the main Harvey .env if it exists
if [ -f /home/azureuser/harvey/.env ]; then
    echo "Loading existing .env file..."
    set -a
    source /home/azureuser/harvey/.env
    set +a
fi

# Export critical environment variables for the sanity check
# These should already be in your environment but let's make sure they're accessible
cat >> /home/azureuser/harvey/.env << 'ENVFILE'

# Ensure these are set for sanity check
export HARVEY_AI_API_KEY="${HARVEY_AI_API_KEY}"
export SENDGRID_API_KEY="${SENDGRID_API_KEY}"
export SQLSERVER_HOST="${SQLSERVER_HOST}"
export SQLSERVER_DB="${SQLSERVER_DB}"
export SQLSERVER_USER="${SQLSERVER_USER}"
export SQLSERVER_PASSWORD="${SQLSERVER_PASSWORD}"
ENVFILE

# Create a system-wide environment file for cron jobs
sudo tee /etc/environment.d/harvey.conf > /dev/null << SYSENV
HARVEY_AI_API_KEY="${HARVEY_AI_API_KEY}"
SENDGRID_API_KEY="${SENDGRID_API_KEY}"
SQLSERVER_HOST="${SQLSERVER_HOST}"
SQLSERVER_DB="${SQLSERVER_DB}"
SQLSERVER_USER="${SQLSERVER_USER}"
SQLSERVER_PASSWORD="${SQLSERVER_PASSWORD}"
ML_API_BASE_URL="${ML_API_BASE_URL}"
INTERNAL_ML_API_KEY="${INTERNAL_ML_API_KEY}"
AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}"
AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT}"
OPENAI_API_KEY="${OPENAI_API_KEY}"
GEMINI_API_KEY="${GEMINI_API_KEY}"
ALERT_EMAIL_TO="dev@heydividend.com"
ALERT_EMAIL_FROM="alerts@harvey-ai.com"
SYSENV

echo "✅ Environment variables configured"

# 2. Fix ML Scheduler Services
echo ""
echo "=================================================="
echo "2. Setting up ML Scheduler Services..."
echo "=================================================="

# Create the main ML scheduler service if it doesn't exist
if [ ! -f /etc/systemd/system/heydividend-ml-schedulers.service ]; then
    echo "Creating ML scheduler service..."
    sudo tee /etc/systemd/system/heydividend-ml-schedulers.service > /dev/null << 'SERVICE'
[Unit]
Description=HeyDividend ML Schedulers
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/ml-service
ExecStart=/home/azureuser/miniconda3/bin/python scheduler_main.py
Restart=on-failure
RestartSec=10
Environment="PATH=/home/azureuser/miniconda3/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/etc/environment.d/harvey.conf

[Install]
WantedBy=multi-user.target
SERVICE
fi

# Create individual timer services (these run Python scripts, not systemd timers)
# Since the timers don't exist, let's create cron jobs instead
echo "Setting up cron jobs for ML schedulers..."

# Remove old cron entries
(crontab -l 2>/dev/null | grep -v "ml_scheduler" | grep -v "harvey_sanity_check") > /tmp/crontab.tmp

# Add ML scheduler jobs
cat >> /tmp/crontab.tmp << 'CRON'
# ML Payout Rating - Daily at 1:00 AM
0 1 * * * cd /home/azureuser/harvey && source .env && /home/azureuser/miniconda3/bin/python -c "from app.services.ml_schedulers_service import MLSchedulersService; s = MLSchedulersService(); s.run_payout_rating_scheduler()" >> /home/azureuser/harvey/logs/ml_payout_rating.log 2>&1

# ML Dividend Calendar - Sunday at 2:00 AM  
0 2 * * 0 cd /home/azureuser/harvey && source .env && /home/azureuser/miniconda3/bin/python -c "from app.services.ml_schedulers_service import MLSchedulersService; s = MLSchedulersService(); s.run_dividend_calendar_scheduler()" >> /home/azureuser/harvey/logs/ml_dividend_calendar.log 2>&1

# ML Training - Sunday at 3:00 AM
0 3 * * 0 cd /home/azureuser/harvey && source .env && /home/azureuser/miniconda3/bin/python -c "from app.services.ml_schedulers_service import MLSchedulersService; s = MLSchedulersService(); s.run_ml_training_scheduler()" >> /home/azureuser/harvey/logs/ml_training.log 2>&1

# Daily Sanity Check - 2:00 AM (updated to source environment)
0 2 * * * cd /home/azureuser/harvey && source .env && /home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py >> /home/azureuser/harvey/logs/sanity_cron.log 2>&1
CRON

# Install the new crontab
crontab /tmp/crontab.tmp
rm /tmp/crontab.tmp

echo "✅ Cron jobs configured for ML schedulers"

# 3. Fix Python script to load environment properly
echo ""
echo "=================================================="
echo "3. Updating sanity check script..."
echo "=================================================="

# Update the sanity check script to load .env file
cat > /tmp/env_loader.py << 'PYTHON'
import os
from pathlib import Path

def load_env_file(env_path="/home/azureuser/harvey/.env"):
    """Load environment variables from .env file"""
    if Path(env_path).exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value

# Load environment at import time
load_env_file()
PYTHON

# Prepend env loader to sanity check script if not already there
if ! grep -q "load_env_file" harvey_sanity_check_v3_with_email.py; then
    cp harvey_sanity_check_v3_with_email.py harvey_sanity_check_v3_with_email.py.bak
    cat /tmp/env_loader.py harvey_sanity_check_v3_with_email.py.bak > harvey_sanity_check_v3_with_email.py
    echo "✅ Updated sanity check script to load environment"
fi

# 4. Install missing Python packages
echo ""
echo "=================================================="
echo "4. Installing required packages..."
echo "=================================================="

/home/azureuser/miniconda3/bin/pip install sendgrid pymssql --quiet
echo "✅ Required packages installed"

# 5. Test environment loading
echo ""
echo "=================================================="
echo "5. Testing environment..."
echo "=================================================="

# Test if environment variables are accessible
/home/azureuser/miniconda3/bin/python << 'TEST'
import os

required_vars = [
    "HARVEY_AI_API_KEY",
    "SENDGRID_API_KEY", 
    "SQLSERVER_HOST",
    "SQLSERVER_DB",
    "SQLSERVER_USER",
    "SQLSERVER_PASSWORD"
]

# Try to load from .env
try:
    from pathlib import Path
    env_path = "/home/azureuser/harvey/.env"
    if Path(env_path).exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value
except:
    pass

missing = []
found = []
for var in required_vars:
    if os.getenv(var):
        found.append(var)
    else:
        missing.append(var)

print(f"✅ Found {len(found)} environment variables")
for var in found:
    value = os.getenv(var)
    if "KEY" in var or "PASSWORD" in var:
        print(f"   {var}: ***{value[-4:] if len(value) > 4 else '***'}")
    else:
        print(f"   {var}: {value}")

if missing:
    print(f"\n⚠️  Missing {len(missing)} variables:")
    for var in missing:
        print(f"   - {var}")
TEST

echo ""
echo "=================================================="
echo "✅ Environment fix complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Run the sanity check manually to verify:"
echo "   cd /home/azureuser/harvey"
echo "   source .env"
echo "   python harvey_sanity_check_v3_with_email.py"
echo ""
echo "2. Check cron jobs:"
echo "   crontab -l"
echo ""
echo "3. View logs:"
echo "   tail -f /home/azureuser/harvey/logs/sanity_check_*.log"
echo ""
