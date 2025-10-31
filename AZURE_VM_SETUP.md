# Azure VM Training Job Management

**Feature:** Simple SSH Client for Azure VM Access  
**Implementation Date:** October 31, 2025

---

## Overview

Harvey now includes a **Simple SSH Client** for managing training jobs on Azure VM. This allows you to execute commands, check GPU status, start training jobs, monitor logs, and transfer files - all through API endpoints.

---

## Setup Instructions

### 1. **Configure Environment Secrets**

Add these three secrets to your Replit environment:

```bash
AZURE_VM_IP=<your-vm-ip-or-hostname>
AZURE_VM_USER=<your-ssh-username>
AZURE_VM_PASSWORD=<your-ssh-password>
```

**Optional:**
```bash
AZURE_VM_PORT=22  # Default is 22, only set if using a different port
```

### 2. **Test Connection**

Check if the VM is accessible:

```bash
curl -X GET "http://your-domain/v1/azure-vm/health" \
  -H "Authorization: Bearer YOUR_HARVEY_API_KEY"
```

**Expected Response:**
```json
{
  "configured": true,
  "healthy": true,
  "message": "Azure VM accessible",
  "host": "20.123.45.67",
  "username": "azureuser"
}
```

---

## API Endpoints

### **1. Health Check**

**Endpoint:** `GET /v1/azure-vm/health`  
**Auth:** None (public endpoint for monitoring)

**Response:**
```json
{
  "configured": true,
  "healthy": true,
  "message": "Azure VM accessible"
}
```

---

### **2. Execute Command**

**Endpoint:** `POST /v1/azure-vm/execute`  
**Auth:** Required (API Key)

**Request:**
```json
{
  "command": "ls -la /home/user/training",
  "timeout": 30
}
```

**Response:**
```json
{
  "success": true,
  "command": "ls -la /home/user/training",
  "stdout": "total 48\ndrwxr-xr-x 3 user user 4096 Oct 31 10:00 .\n...",
  "stderr": "",
  "exit_code": 0
}
```

---

### **3. Check GPU Status**

**Endpoint:** `GET /v1/azure-vm/gpu-status`  
**Auth:** Required (API Key)

**Response:**
```json
{
  "success": true,
  "gpu_info": "Thu Oct 31 10:15:23 2025\n+-----------------------------------------------------------------------------+\n| NVIDIA-SMI 525.125.06   Driver Version: 525.125.06   CUDA Version: 12.0     |\n|-------------------------------+----------------------+----------------------+\n| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |\n| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |\n|===============================+======================+======================|\n|   0  NVIDIA A100        On   | 00000000:00:04.0 Off |                    0 |\n| N/A   34C    P0    45W / 250W |      0MiB / 40960MiB |      0%      Default |\n+-------------------------------+----------------------+----------------------+",
  "error": null
}
```

---

### **4. Check System Resources**

**Endpoint:** `GET /v1/azure-vm/system-resources`  
**Auth:** Required (API Key)

**Response:**
```json
{
  "success": true,
  "resources": "=== CPU INFO ===\ntop - 10:15:45 up 5 days,  3:24,  1 user,  load average: 0.15, 0.20, 0.25\n\n=== MEMORY INFO ===\n              total        used        free      shared  buff/cache   available\nMem:           62Gi       12Gi        45Gi       1.0Gi       5.0Gi        48Gi\n\n=== DISK USAGE ===\nFilesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       500G  120G  380G  24% /\n\n=== GPU INFO ===\nindex, name, utilization.gpu [%], memory.used [MiB], memory.total [MiB]\n0, NVIDIA A100, 0 %, 0 MiB, 40960 MiB",
  "error": null
}
```

---

### **5. List Training Jobs**

**Endpoint:** `GET /v1/azure-vm/training-jobs`  
**Auth:** Required (API Key)

**Response:**
```json
{
  "success": true,
  "jobs": "user     12345  0.0  0.1 123456 78901 ?        S    10:00   0:05 python train_model.py --epochs 100\nuser     12346  1.2  5.3 567890 123456 ?        R    10:05   2:30 python train_transformer.py --batch-size 32",
  "error": null
}
```

---

### **6. Start Training Job**

**Endpoint:** `POST /v1/azure-vm/start-training`  
**Auth:** Required (API Key)

**Request:**
```json
{
  "script_path": "/home/user/ml-training/train.py",
  "args": "--epochs 100 --batch-size 32 --lr 0.001"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Training job started successfully",
  "script_path": "/home/user/ml-training/train.py",
  "args": "--epochs 100 --batch-size 32 --lr 0.001",
  "output": "",
  "error": null
}
```

---

### **7. Tail Training Log**

**Endpoint:** `POST /v1/azure-vm/tail-log`  
**Auth:** Required (API Key)

**Request:**
```json
{
  "log_file": "/home/user/ml-training/training.log",
  "lines": 50
}
```

**Response:**
```json
{
  "success": true,
  "log_file": "/home/user/ml-training/training.log",
  "lines": 50,
  "content": "Epoch 45/100\nLoss: 0.0234\nAccuracy: 0.9567\n...",
  "error": null
}
```

---

### **8. Check Disk Usage**

**Endpoint:** `GET /v1/azure-vm/disk-usage`  
**Auth:** Required (API Key)

**Response:**
```json
{
  "success": true,
  "disk_usage": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       500G  120G  380G  24% /\ntmpfs            31G     0   31G   0% /dev/shm",
  "error": null
}
```

---

## Python Client Usage

### **Quick Examples:**

```python
from app.utils.azure_vm_client import get_vm_client

# Get VM client
vm_client = get_vm_client()

# Execute any command
success, stdout, stderr = vm_client.execute_command("nvidia-smi")
print(stdout)

# Check GPU status
success, gpu_info, error = vm_client.check_gpu_status()
print(gpu_info)

# Start training job
success, output, error = vm_client.start_training_job(
    "/home/user/train.py", 
    "--epochs 100"
)

# Tail logs
success, logs, error = vm_client.tail_log("training.log", lines=100)
print(logs)

# Check system resources
success, resources, error = vm_client.check_system_resources()
print(resources)
```

---

## Use Cases

### **1. Monitor Training Progress**

```bash
# Check if training is running
curl -X GET "http://your-domain/v1/azure-vm/training-jobs" \
  -H "Authorization: Bearer YOUR_API_KEY"

# View latest logs
curl -X POST "http://your-domain/v1/azure-vm/tail-log" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"log_file": "training.log", "lines": 100}'
```

### **2. Start Training on Demand**

```bash
curl -X POST "http://your-domain/v1/azure-vm/start-training" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "script_path": "/home/user/ml/train.py",
    "args": "--model transformer --epochs 50"
  }'
```

### **3. Monitor GPU Utilization**

```bash
# Get GPU status
curl -X GET "http://your-domain/v1/azure-vm/gpu-status" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get full system resources
curl -X GET "http://your-domain/v1/azure-vm/system-resources" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### **4. Run Custom Commands**

```bash
# List files in training directory
curl -X POST "http://your-domain/v1/azure-vm/execute" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -lh /home/user/models/*.pth"}'

# Check Python packages
curl -X POST "http://your-domain/v1/azure-vm/execute" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command": "pip list | grep torch"}'
```

---

## Security Notes

✅ **Password Authentication** - Uses SSH password (stored securely as Replit secrets)  
✅ **API Key Protection** - All endpoints (except health check) require Harvey API key  
✅ **Auto-Close Connections** - SSH connections automatically close after command execution  
✅ **Timeout Protection** - All commands have configurable timeouts (default: 30s, max: 300s)  
✅ **Audit Logging** - All commands are logged with timestamps  

---

## Troubleshooting

### **Issue: "Azure VM client not configured"**

**Solution:** Set the required environment variables:
```bash
AZURE_VM_IP=your-vm-ip
AZURE_VM_USER=your-username
AZURE_VM_PASSWORD=your-password
```

### **Issue: "Authentication failed"**

**Possible causes:**
- Wrong username or password
- VM firewall blocking SSH (port 22)
- Network connectivity issues

**Solution:**
1. Test SSH manually: `ssh user@vm-ip`
2. Check Azure VM firewall/NSG rules (allow port 22)
3. Verify credentials are correct

### **Issue: "Connection timeout"**

**Possible causes:**
- VM is down or unreachable
- Network issues
- SSH service not running

**Solution:**
1. Check VM is running in Azure portal
2. Verify SSH service: `systemctl status sshd`
3. Test network connectivity: `ping vm-ip`

---

## Advanced Usage

### **File Transfer (Future Enhancement)**

The client includes file transfer methods, but they're not yet exposed via API:

```python
# Upload file
vm_client.upload_file(
    "/local/path/model.pth", 
    "/remote/path/model.pth"
)

# Download file
vm_client.download_file(
    "/remote/path/results.csv", 
    "/local/path/results.csv"
)
```

To expose these, add new endpoints to `app/routes/azure_vm.py`.

---

## Files Created

1. **`app/utils/azure_vm_client.py`** - SSH client utility
2. **`app/routes/azure_vm.py`** - FastAPI router with 8 endpoints
3. **`main.py`** - Registered Azure VM router
4. **`requirements.txt`** - Added paramiko dependency
5. **`AZURE_VM_SETUP.md`** - This documentation

---

## Next Steps

1. **Set up secrets** - Add `AZURE_VM_IP`, `AZURE_VM_USER`, `AZURE_VM_PASSWORD`
2. **Test connection** - Hit the `/v1/azure-vm/health` endpoint
3. **Run your first command** - Use `/v1/azure-vm/execute` to test
4. **Start managing training jobs!** 🚀

---

**Status:** ✅ Ready to use  
**API Version:** v1  
**Last Updated:** October 31, 2025
