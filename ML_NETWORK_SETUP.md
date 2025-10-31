# ML API Network Configuration Guide

## Problem Description

The ML API deployed to Azure VM at `20.81.210.213:9000` is timing out when accessed from Harvey's Replit environment. Connection attempts result in timeout errors after 120 seconds.

**Symptoms:**
- ML API requests timeout with error: `timed out`
- Circuit breaker opens after 5 consecutive failures
- Logs show: `ML API timeout for /score/symbol`, `/predict/growth-rate`, etc.

**Root Cause:**
Network connectivity issue - likely due to Azure Network Security Group (NSG) or VM firewall blocking inbound traffic on port 9000.

---

## Solution: Configure Azure Network Access

### Step 1: Configure Azure Network Security Group (NSG)

The Azure NSG controls inbound and outbound traffic at the network level. You need to add a rule to allow traffic on port 9000.

#### Option A: Using Azure Portal

1. **Navigate to your VM's Network Security Group:**
   - Go to Azure Portal → Virtual Machines
   - Select your VM (`HeyDividend-ML-Server` or similar)
   - Click on "Networking" in the left menu
   - Click on the Network Security Group name

2. **Add Inbound Security Rule:**
   - Click "Inbound security rules" in the left menu
   - Click "+ Add" at the top
   - Configure the rule:
     ```
     Source:                Any
     Source port ranges:    *
     Destination:           Any
     Service:               Custom
     Destination port ranges: 9000
     Protocol:              TCP
     Action:                Allow
     Priority:              1000
     Name:                  Allow-ML-API-9000
     Description:           Allow inbound traffic for ML API on port 9000
     ```
   - Click "Add"

3. **Verify the rule:**
   - The rule should appear in the list of inbound security rules
   - Status should show as "Active"

#### Option B: Using Azure CLI

```bash
# Get your resource group and NSG name
az vm show --name <YOUR_VM_NAME> --resource-group <YOUR_RESOURCE_GROUP> --query "networkProfile.networkInterfaces[0].id" -o tsv

# Add the inbound rule
az network nsg rule create \
  --resource-group <YOUR_RESOURCE_GROUP> \
  --nsg-name <YOUR_NSG_NAME> \
  --name Allow-ML-API-9000 \
  --priority 1000 \
  --source-address-prefixes '*' \
  --source-port-ranges '*' \
  --destination-address-prefixes '*' \
  --destination-port-ranges 9000 \
  --access Allow \
  --protocol Tcp \
  --description "Allow inbound traffic for ML API on port 9000"
```

---

### Step 2: Configure VM Firewall (UFW)

Even with NSG configured, the VM's internal firewall (UFW - Uncomplicated Firewall) may still block the port.

#### Connect to your Azure VM:

```bash
# SSH into your Azure VM
ssh azureuser@20.81.210.213
```

#### Configure UFW:

```bash
# Check UFW status
sudo ufw status

# Allow port 9000
sudo ufw allow 9000/tcp

# Verify the rule was added
sudo ufw status numbered

# If UFW is inactive, you can enable it (optional, but be careful)
# Make sure SSH port 22 is allowed first!
sudo ufw allow 22/tcp
sudo ufw enable
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
9000/tcp                   ALLOW       Anywhere
22/tcp (v6)                ALLOW       Anywhere (v6)
9000/tcp (v6)              ALLOW       Anywhere (v6)
```

---

### Step 3: Verify ML API is Listening on 0.0.0.0:9000

The ML API must listen on `0.0.0.0:9000` (all network interfaces), not just `127.0.0.1:9000` (localhost only).

#### Check current listening status:

```bash
# SSH into your Azure VM
ssh azureuser@20.81.210.213

# Check what's listening on port 9000
sudo netstat -tulpn | grep 9000
# OR
sudo ss -tulpn | grep 9000
# OR
sudo lsof -i :9000
```

**Good output (listening on all interfaces):**
```
tcp        0      0 0.0.0.0:9000            0.0.0.0:*               LISTEN      12345/python3
```

**Bad output (listening on localhost only):**
```
tcp        0      0 127.0.0.1:9000          0.0.0.0:*               LISTEN      12345/python3
```

#### If listening on 127.0.0.1 only, update your ML API configuration:

**For Flask applications:**
```python
# In your ML API main.py or app.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)  # NOT host="127.0.0.1"
```

**For FastAPI/Uvicorn:**
```bash
uvicorn main:app --host 0.0.0.0 --port 9000
```

**For Gunicorn:**
```bash
gunicorn --bind 0.0.0.0:9000 main:app
```

#### Restart your ML API service:

```bash
# If using systemd
sudo systemctl restart ml-api

# If running manually, stop and restart
pkill -f "python.*ml.*api"
nohup python3 main.py > ml_api.log 2>&1 &
```

---

### Step 4: Test Network Connectivity

#### Test from the Azure VM itself (localhost):

```bash
# SSH into your Azure VM
ssh azureuser@20.81.210.213

# Test local connection
curl http://localhost:9000/health
curl http://127.0.0.1:9000/health
```

**Expected output:**
```json
{"status": "healthy"}
```

#### Test from the Azure VM using public IP:

```bash
# Still on the Azure VM
curl http://20.81.210.213:9000/health
```

This tests if the firewall allows traffic from the public IP.

#### Test from Replit environment:

```bash
# In Replit Shell
curl -v http://20.81.210.213:9000/health

# Or with timeout
curl --max-time 10 http://20.81.210.213:9000/health
```

**Expected output:**
```json
{"status": "healthy"}
```

#### Test from your local machine:

```bash
# From your local terminal
curl http://20.81.210.213:9000/health
```

#### Advanced testing with telnet:

```bash
# Test if port is open (from Replit or local machine)
telnet 20.81.210.213 9000
# If successful, you'll see "Connected to 20.81.210.213"
# Press Ctrl+] then type "quit" to exit

# OR use nc (netcat)
nc -zv 20.81.210.213 9000
```

**Successful output:**
```
Connection to 20.81.210.213 9000 port [tcp/*] succeeded!
```

---

## Verification Checklist

After completing the above steps, verify:

- [ ] Azure NSG has inbound rule allowing port 9000
- [ ] VM firewall (UFW) allows port 9000
- [ ] ML API is listening on `0.0.0.0:9000` (not `127.0.0.1:9000`)
- [ ] `curl http://localhost:9000/health` works on the VM
- [ ] `curl http://20.81.210.213:9000/health` works on the VM
- [ ] `curl http://20.81.210.213:9000/health` works from Replit
- [ ] Harvey API Server shows ML API requests succeeding in logs
- [ ] Circuit breaker is CLOSED (not OPEN)

---

## Common Issues & Troubleshooting

### Issue 1: NSG rule not taking effect
- **Solution:** Wait 1-2 minutes after creating the rule for it to propagate
- **Verify:** Check NSG rule status is "Active"

### Issue 2: UFW blocking despite allowing port 9000
- **Solution:** Check UFW rule order with `sudo ufw status numbered`
- **Fix:** Ensure allow rules come before deny rules

### Issue 3: ML API still listening on 127.0.0.1
- **Solution:** Update application code to bind to `0.0.0.0`
- **Verify:** `sudo netstat -tulpn | grep 9000` shows `0.0.0.0:9000`

### Issue 4: Connection refused vs. Connection timeout
- **Connection refused:** Service is not running or listening on wrong interface
- **Connection timeout:** Firewall/NSG blocking traffic
- **Solution:** Use appropriate troubleshooting steps from above

### Issue 5: Works from VM but not from Replit
- **Likely cause:** NSG not configured or VM has multiple network interfaces
- **Solution:** Double-check NSG configuration and ensure rule applies to correct subnet

---

## Testing ML API Health from Harvey

Once network access is configured, Harvey will automatically start using the ML API. You can verify by:

### 1. Check Harvey Logs

Look for successful ML API requests:
```
[INFO] ML API request: /score/symbol with 1 symbols
[INFO] ML quality score: JNJ = 87.5 (A+)
```

### 2. Monitor Circuit Breaker Status

Healthy status:
```
[INFO] Circuit breaker CLOSED: 0 failures
```

Unhealthy status (before fix):
```
[WARNING] Circuit breaker OPEN: 5 consecutive failures
```

### 3. Test ML Endpoints Manually

From Replit Shell:
```bash
# Health check
curl http://20.81.210.213:9000/api/internal/ml/health

# Score endpoint
curl -X POST http://20.81.210.213:9000/api/internal/ml/score/symbol \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL"]}'
```

---

## Additional Security Recommendations

### Restrict Source IP (Optional but Recommended)

Instead of allowing `Any` source, restrict to Replit's IP ranges:

1. **Find Replit's outbound IP:**
   ```bash
   # In Replit Shell
   curl https://api.ipify.org
   ```

2. **Update NSG rule to allow only that IP:**
   ```bash
   az network nsg rule update \
     --resource-group <YOUR_RESOURCE_GROUP> \
     --nsg-name <YOUR_NSG_NAME> \
     --name Allow-ML-API-9000 \
     --source-address-prefixes '<REPLIT_IP>/32'
   ```

### Use HTTPS (Recommended for Production)

For production deployments, consider:
1. Setting up SSL/TLS certificates (Let's Encrypt)
2. Running ML API behind nginx with HTTPS
3. Updating Harvey to use `https://20.81.210.213:9443` instead

---

## Summary

The ML API network timeout issue is caused by network-level blocking. Follow these steps in order:

1. ✅ Configure Azure NSG to allow port 9000
2. ✅ Configure VM firewall (UFW) to allow port 9000  
3. ✅ Ensure ML API listens on `0.0.0.0:9000`
4. ✅ Test connectivity from multiple sources
5. ✅ Verify Harvey logs show successful ML API requests

Once configured correctly, Harvey will automatically integrate ML intelligence into all dividend analysis queries.
