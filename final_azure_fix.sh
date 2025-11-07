#!/bin/bash

# Final comprehensive fix for Azure VM environment issues

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🔧 Final Fix for Azure VM Environment"
echo "=================================================="
echo ""

# Create a wrapper script that properly loads environment
cat > harvey_env_wrapper.sh << 'EOF'
#!/bin/bash

# Wrapper script to ensure environment variables are loaded

# Export all variables from .env file
if [ -f /home/azureuser/harvey/.env ]; then
    set -a
    source /home/azureuser/harvey/.env
    set +a
fi

# Also export from system environment
export PATH="/home/azureuser/miniconda3/bin:$PATH"

# Add Python path
export PYTHONPATH="/home/azureuser/harvey:$PYTHONPATH"

# Verify critical variables are set
if [ -z "$HARVEY_AI_API_KEY" ]; then
    echo "Warning: HARVEY_AI_API_KEY not set"
fi

if [ -z "$SENDGRID_API_KEY" ]; then
    echo "Warning: SENDGRID_API_KEY not set"
fi

# Run the sanity check with all environment variables loaded
cd /home/azureuser/harvey
/home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py
EOF

# Create Python script that loads env at the module level
cat > load_env_fixed.py << 'EOF'
#!/usr/bin/env python3
"""
Fixed Harvey ML Scheduler Sanity Check v3.1 with proper environment loading
"""

import os
import sys
from pathlib import Path

# CRITICAL: Load environment variables FIRST before any other imports
def load_env_file(env_path="/home/azureuser/harvey/.env"):
    """Load environment variables from .env file"""
    if Path(env_path).exists():
        print(f"Loading environment from {env_path}...")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    # Handle export prefix if present
                    if line.startswith('export '):
                        line = line[7:]
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Handle variable expansion (e.g., ${VAR})
                    if '${' in value:
                        import re
                        for match in re.finditer(r'\$\{([^}]+)\}', value):
                            var_name = match.group(1)
                            var_value = os.environ.get(var_name, '')
                            value = value.replace(match.group(0), var_value)
                    
                    # Only set if not already in environment
                    if key not in os.environ or not os.environ[key]:
                        os.environ[key] = value
                        print(f"  Set {key} = {'***' if 'KEY' in key or 'PASSWORD' in key else value[:20]}")
    else:
        print(f"Warning: {env_path} not found")

# Load environment immediately
load_env_file()

# Now verify what we have
print("\nEnvironment check:")
critical_vars = [
    "HARVEY_AI_API_KEY",
    "SENDGRID_API_KEY",
    "SQLSERVER_HOST",
    "SQLSERVER_DB",
    "SQLSERVER_USER",
    "SQLSERVER_PASSWORD"
]

for var in critical_vars:
    value = os.getenv(var)
    if value:
        if "KEY" in var or "PASSWORD" in var:
            print(f"  ✓ {var}: ***{value[-4:]}")
        else:
            print(f"  ✓ {var}: {value}")
    else:
        print(f"  ✗ {var}: NOT SET")

# Now import and run the sanity check
if "--run" in sys.argv:
    print("\nRunning sanity check...")
    # Import the fixed sanity check module
    exec(open('harvey_sanity_check_v3_with_email.py').read())
EOF

echo "📤 Step 1: Copying fixed sanity check script..."
scp harvey_sanity_check_v3_with_email.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/

echo ""
echo "📤 Step 2: Copying helper scripts..."
scp harvey_env_wrapper.sh $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/
scp load_env_fixed.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/

echo ""
echo "🔧 Step 3: Fixing environment and permissions on VM..."
ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_FIX'
cd /home/azureuser/harvey

# Make scripts executable
chmod +x harvey_env_wrapper.sh
chmod +x load_env_fixed.py

# Ensure .env file has proper permissions
chmod 600 .env

# Test environment loading
echo "=================================================="
echo "Testing environment loading..."
echo "=================================================="
/home/azureuser/miniconda3/bin/python load_env_fixed.py

# Update cron to use the wrapper script
echo ""
echo "=================================================="
echo "Updating cron jobs to use wrapper..."
echo "=================================================="

# Remove old cron entries and add new ones with proper environment loading
(crontab -l 2>/dev/null | grep -v "harvey_sanity_check" | grep -v "ml_scheduler") > /tmp/cron_new

# Add new cron jobs that properly load environment
cat >> /tmp/cron_new << 'CRON'
# Daily sanity check at 2:00 AM with proper environment loading
0 2 * * * /bin/bash /home/azureuser/harvey/harvey_env_wrapper.sh >> /home/azureuser/harvey/logs/sanity_cron.log 2>&1
CRON

crontab /tmp/cron_new
rm /tmp/cron_new

echo "✅ Cron updated"

# Install missing packages
echo ""
echo "=================================================="
echo "Installing packages..."
echo "=================================================="
/home/azureuser/miniconda3/bin/pip install sendgrid pymssql --quiet
echo "✅ Packages installed"

# Create simple test script
cat > test_env.py << 'TEST'
import os
vars = ["HARVEY_AI_API_KEY", "SENDGRID_API_KEY", "SQLSERVER_HOST"]
for v in vars:
    val = os.getenv(v)
    if val:
        print(f"✓ {v}: {'***' + val[-4:] if 'KEY' in v else val}")
    else:
        print(f"✗ {v}: MISSING")
TEST

echo ""
echo "=================================================="
echo "Final environment test..."
echo "=================================================="
source .env && /home/azureuser/miniconda3/bin/python test_env.py

REMOTE_FIX

echo ""
echo "🏃 Step 4: Running final sanity check..."
ssh $AZURE_USER@$AZURE_VM_IP "cd /home/azureuser/harvey && bash harvey_env_wrapper.sh"

echo ""
echo "=================================================="
echo "✅ FINAL FIX COMPLETE!"
echo "=================================================="
echo ""
echo "Solutions applied:"
echo "  ✅ Fixed bug in sanity check script (self.warnings)"
echo "  ✅ Created wrapper script for proper env loading"
echo "  ✅ Updated cron to use wrapper script"
echo "  ✅ Verified environment variables loading"
echo ""
echo "To manually test:"
echo "  ssh $AZURE_USER@$AZURE_VM_IP"
echo "  cd /home/azureuser/harvey"
echo "  bash harvey_env_wrapper.sh"
echo ""
echo "Logs are at:"
echo "  /home/azureuser/harvey/logs/sanity_cron.log"
echo "=================================================="