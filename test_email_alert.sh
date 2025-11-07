#!/bin/bash

# Test email alerts with updated SendGrid key

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

# Check if SSH_VM_PASSWORD is set
if [ -z "$SSH_VM_PASSWORD" ]; then
    echo "❌ ERROR: SSH_VM_PASSWORD not set"
    exit 1
fi

echo "=================================================="
echo "📧 Testing Email Alerts with Updated SendGrid Key"
echo "=================================================="
echo ""

# Update SendGrid key on Azure VM and test email
sshpass -p "$SSH_VM_PASSWORD" ssh -o StrictHostKeyChecking=no $AZURE_USER@$AZURE_VM_IP << 'REMOTE_TEST'
cd /home/azureuser/harvey

echo "📝 Updating SendGrid API key in .env file..."

# Backup current .env
cp .env .env.backup

# Update SendGrid key with the new one
if [ -f .env ]; then
    # Remove old SendGrid key line
    grep -v "^SENDGRID_API_KEY=" .env > .env.tmp
    mv .env.tmp .env
fi

# Add the updated SendGrid key
echo "SENDGRID_API_KEY=$SENDGRID_API_KEY" >> .env

echo "✅ SendGrid key updated"
echo ""

# Test email sending with a Python script
echo "🧪 Testing email functionality..."
cat > test_sendgrid.py << 'PYTHON'
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Load environment
from pathlib import Path
env_path = Path('.env')
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value

# Get SendGrid key
sg_key = os.getenv('SENDGRID_API_KEY')
if not sg_key:
    print("❌ SendGrid API key not found in environment")
    exit(1)

print(f"✓ SendGrid key loaded: {sg_key[:7]}...{sg_key[-4:]}")

try:
    # Create message
    message = Mail(
        from_email='alerts@harvey-ai.com',
        to_emails='dev@heydividend.com',
        subject='[TEST] Harvey Email Alerts Working!',
        html_content='''
        <div style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    ✅ Email Alerts Successfully Configured!
                </h2>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    Great news! Your Harvey AI email alerts are now working correctly.
                </p>
                <div style="background: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                    <strong>System Status:</strong><br>
                    • SendGrid API: Connected ✅<br>
                    • Recipient: dev@heydividend.com<br>
                    • Sender: alerts@harvey-ai.com<br>
                    • Daily Alerts: 2:00 AM
                </div>
                <p style="color: #555;">
                    You'll receive alerts whenever:
                </p>
                <ul style="color: #555;">
                    <li>System health drops below 80%</li>
                    <li>Critical services fail</li>
                    <li>Database issues occur</li>
                    <li>ML schedulers encounter errors</li>
                </ul>
                <p style="color: #888; font-size: 14px; margin-top: 30px;">
                    This is a test email from your Harvey AI system on Azure VM.
                </p>
            </div>
        </div>
        '''
    )
    
    # Send email
    sg = SendGridAPIClient(sg_key)
    response = sg.send(message)
    
    print(f"✅ Email sent successfully!")
    print(f"   Status Code: {response.status_code}")
    print(f"   Message ID: {response.headers.get('X-Message-Id', 'N/A')}")
    print(f"   Recipient: dev@heydividend.com")
    
except Exception as e:
    print(f"❌ Failed to send email: {e}")
    exit(1)
PYTHON

# Run the test
/home/azureuser/miniconda3/bin/python test_sendgrid.py

echo ""
echo "=================================================="
echo "📧 Now running full sanity check with email alerts..."
echo "=================================================="

# Run sanity check which will send email if issues found
./run_with_env.sh /home/azureuser/miniconda3/bin/python harvey_sanity_check_v3_with_email.py

REMOTE_TEST

echo ""
echo "=================================================="
echo "✅ EMAIL TEST COMPLETE!"
echo "=================================================="
echo ""
echo "If successful, you should receive:"
echo "  1. Test email confirming setup"
echo "  2. Sanity check email (if health < 80%)"
echo ""
echo "Check your inbox at: dev@heydividend.com"
echo "=================================================="