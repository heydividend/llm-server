# Direct Deployment Commands for ML Scheduler

Since you're getting password prompts, here are the direct commands to run after SSHing into your Azure VM.

## Option 1: Direct SSH Session (Recommended)

First, SSH into your Azure VM:
```bash
ssh azureuser@20.81.210.213
```

Then run these commands directly on the VM:

### Step 1: Navigate to Harvey directory
```bash
cd /home/azureuser/harvey
```

### Step 2: Create backup
```bash
cp main.py main.py.backup_ml_scheduler
```

### Step 3: Copy the ML scheduler files from Replit
Since you're in Replit, you'll need to manually copy these files to the VM. 
Here's the content to create on the VM:

#### Create /home/azureuser/harvey/app/routes/ml_schedulers.py:
```bash
nano app/routes/ml_schedulers.py
```

Copy this content (from your Replit app/routes/ml_schedulers.py) and paste it.

#### Create /home/azureuser/harvey/app/services/ml_schedulers_service.py:
```bash
nano app/services/ml_schedulers_service.py
```

Copy this content (from your Replit app/services/ml_schedulers_service.py) and paste it.

### Step 4: Update main.py to register the routes
```bash
# Open main.py in nano
nano main.py
```

Add these two lines:

1. After the other imports (around line 15-20), add:
```python
from app.routes import ml_schedulers
```

2. After the chat router registration (around line 80-100), add:
```python
app.include_router(ml_schedulers.router, prefix="/v1", tags=["ML Schedulers"])
```

Save and exit (Ctrl+X, Y, Enter)

### Step 5: Install dependencies
```bash
source venv/bin/activate
pip install aiohttp
```

### Step 6: Restart the service
```bash
sudo systemctl restart harvey
```

### Step 7: Check if it's working
```bash
# Check service status
sudo systemctl status harvey

# Test the endpoint
curl http://localhost:8001/v1/ml-schedulers/health
```

## Option 2: Setup SSH Key (For Future Deployments)

To avoid password prompts in the future:

```bash
# On your local machine (Replit):
ssh-keygen -t rsa -b 4096 -f ~/.ssh/azure_vm_key

# Copy the public key
cat ~/.ssh/azure_vm_key.pub

# SSH into VM with password one more time
ssh azureuser@20.81.210.213

# On the VM, add the key:
mkdir -p ~/.ssh
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

## Option 3: Use SCP with Password

If you want to copy files directly from Replit:

```bash
# You'll be prompted for password for each file
scp app/routes/ml_schedulers.py azureuser@20.81.210.213:/home/azureuser/harvey/app/routes/
scp app/services/ml_schedulers_service.py azureuser@20.81.210.213:/home/azureuser/harvey/app/services/
scp app/core/self_healing.py azureuser@20.81.210.213:/home/azureuser/harvey/app/core/
```

Then SSH in and update main.py as shown above.

## Quick Test After Deployment

```bash
# From your local machine, test with your API key:
curl http://20.81.210.213:8001/v1/ml-schedulers/health \
  -H "Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key"
```

If successful, you should get a JSON response instead of 404.