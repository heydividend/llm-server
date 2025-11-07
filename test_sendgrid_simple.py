#!/usr/bin/env python3
# Simple SendGrid test following official documentation

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Set the API key directly for testing
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

if not SENDGRID_API_KEY:
    print("ERROR: SENDGRID_API_KEY not found in environment")
    exit(1)

print(f"Testing SendGrid with key format: {SENDGRID_API_KEY[:10]}...")

message = Mail(
    from_email='alerts@harvey-ai.com',
    to_emails='dev@heydividend.com',
    subject='Harvey AI - Email Alerts Working!',
    html_content='<strong>Success!</strong> Your Harvey AI email alerts are now configured correctly.')

try:
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"✅ Email sent successfully!")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Body: {response.body}")
    print(f"   Headers: {response.headers}")
except Exception as e:
    print(f"❌ Error sending email: {str(e)}")