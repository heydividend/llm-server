#!/bin/bash

# Manual SSH commands to fix ML scheduler deployment
# Run these commands after SSHing into your Azure VM

cat << 'INSTRUCTIONS'
==================================================
📝 Manual Fix Instructions for Azure VM
==================================================

Step 1: SSH into your Azure VM
--------------------------------
ssh azureuser@20.81.210.213
(Enter your password)

Step 2: Once logged in, run these commands
-------------------------------------------

cd /home/azureuser/harvey

# Check if the files exist
ls -la app/routes/ml_schedulers.py
ls -la app/services/ml_schedulers_service.py

# If files don't exist, we need to copy them from Replit

# Edit main.py to add the routes
nano main.py

# Find the line with "from app.routes import chat" (around line 15-20)
# Add this line right after it:
from app.routes import ml_schedulers

# Find the line with "app.include_router(chat.router" (around line 100)
# Add this line right after it:
app.include_router(ml_schedulers.router, prefix="/v1", tags=["ML Schedulers"])

# Save and exit (Ctrl+X, Y, Enter)

# Install dependencies
source venv/bin/activate
pip install aiohttp

# Restart the service
sudo systemctl restart harvey

# Wait 5 seconds
sleep 5

# Check if it worked
curl http://localhost:8001/v1/ml-schedulers/health

# If you get {"detail":"Unauthorized"} - SUCCESS! (needs API key)
# If you get {"detail":"Not Found"} - The route isn't registered

# Exit the SSH session
exit

Step 3: Test from your local machine
-------------------------------------
curl http://20.81.210.213:8001/v1/ml-schedulers/health \
  -H "Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key"

==================================================
INSTRUCTIONS