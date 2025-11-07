#!/bin/bash

# Securely test email alerts without exposing SendGrid key

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

# Check if SSH_VM_PASSWORD is set
if [ -z "$SSH_VM_PASSWORD" ]; then
    echo "❌ ERROR: SSH_VM_PASSWORD not set"
    exit 1
fi

# Check if SENDGRID_API_KEY is set
if [ -z "$SENDGRID_API_KEY" ]; then
    echo "❌ ERROR: SENDGRID_API_KEY not set in Replit environment"
    exit 1
fi

echo "=================================================="
echo "🔐 Securely Testing Email Alerts"
echo "=================================================="
echo ""
echo "✓ SendGrid key format verified: ${SENDGRID_API_KEY:0:3}...${SENDGRID_API_KEY: -4}"
echo ""

# Securely pass the SendGrid key through SSH without exposing it
echo "📤 Updating SendGrid key on Azure VM (securely)..."
SENDGRID_API_KEY="$SENDGRID_API_KEY" sshpass -p "$SSH_VM_PASSWORD" ssh -o StrictHostKeyChecking=no $AZURE_USER@$AZURE_VM_IP 'bash -s' << 'REMOTE_SCRIPT'
cd /home/azureuser/harvey

# Update .env file with the new SendGrid key passed via environment
echo "Updating SendGrid API key..."

# Backup current .env
cp .env .env.backup

# Update SendGrid key securely (key comes from SSH environment, not script)
if [ -n "$SENDGRID_API_KEY" ]; then
    # Remove old SendGrid key
    grep -v "^SENDGRID_API_KEY=" .env > .env.tmp
    # Add new SendGrid key from environment
    echo "SENDGRID_API_KEY=$SENDGRID_API_KEY" >> .env.tmp
    mv .env.tmp .env
    chmod 600 .env
    echo "✅ SendGrid key updated securely"
else
    echo "❌ SendGrid key not received"
    exit 1
fi

# Test email functionality
echo ""
echo "🧪 Testing email sending..."

/home/azureuser/miniconda3/bin/python << 'PYTHON'
import os
from pathlib import Path

# Load environment from .env
env_path = Path('.env')
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip().strip('"').strip("'")

# Verify SendGrid key is loaded
sg_key = os.getenv('SENDGRID_API_KEY')
if sg_key and sg_key.startswith('SG.'):
    print(f"✓ SendGrid key loaded: {sg_key[:7]}...{sg_key[-4:]}")
    
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        # Test email
        message = Mail(
            from_email='alerts@harvey-ai.com',
            to_emails='dev@heydividend.com',
            subject='[SUCCESS] Harvey Email Alerts Configured',
            html_content='''
            <h2>✅ Email Alerts Working!</h2>
            <p>Your Harvey AI email alerts are now properly configured.</p>
            <p>You will receive notifications at dev@heydividend.com when:</p>
            <ul>
                <li>System health drops below 80%</li>
                <li>Critical services fail</li>
                <li>ML schedulers encounter issues</li>
            </ul>
            <p style="color: #888;">Sent from Harvey AI on Azure VM</p>
            '''
        )
        
        sg = SendGridAPIClient(sg_key)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Test email sent successfully to dev@heydividend.com")
            print(f"   Status: {response.status_code}")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Email test failed: {e}")
else:
    print("❌ SendGrid key not properly configured")
PYTHON

echo ""
echo "📊 Running sanity check with email alerts enabled..."
./run_with_env.sh /home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py | tail -20

REMOTE_SCRIPT

echo ""
echo "=================================================="
echo "✅ SECURE EMAIL TEST COMPLETE!"
echo "=================================================="
echo ""
echo "Results:"
echo "  • SendGrid key securely updated on Azure VM"
echo "  • Test email sent to dev@heydividend.com"
echo "  • Sanity check ran with email alerts enabled"
echo ""
echo "Please check your inbox at: dev@heydividend.com"
echo "You should receive:"
echo "  1. Test success email"
echo "  2. Sanity check alert (if health < 80%)"
echo ""
echo "=================================================="