# Azure VM Quick Start Guide

## 🚀 **Setup (3 Steps)**

### **1. Add Secrets**
Go to Replit Secrets and add:
```
AZURE_VM_IP = your-vm-ip-address
AZURE_VM_USER = your-username  
AZURE_VM_PASSWORD = your-password
```

### **2. Test Connection**
```bash
curl http://your-domain/v1/azure-vm/health
```

### **3. Start Using!**
You're ready to manage training jobs! ✅

---

## 📚 **Common Commands**

### **Check GPU Status**
```bash
curl -X GET "http://your-domain/v1/azure-vm/gpu-status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### **Start Training Job**
```bash
curl -X POST "http://your-domain/v1/azure-vm/start-training" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "script_path": "/path/to/train.py",
    "args": "--epochs 100 --batch-size 32"
  }'
```

### **View Training Logs**
```bash
curl -X POST "http://your-domain/v1/azure-vm/tail-log" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"log_file": "training.log", "lines": 100}'
```

### **List Running Jobs**
```bash
curl -X GET "http://your-domain/v1/azure-vm/training-jobs" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### **Check System Resources**
```bash
curl -X GET "http://your-domain/v1/azure-vm/system-resources" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### **Execute Any Command**
```bash
curl -X POST "http://your-domain/v1/azure-vm/execute" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command": "df -h"}'
```

---

## 🎯 **8 API Endpoints Available**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/azure-vm/health` | GET | Check VM connection (no auth) |
| `/v1/azure-vm/execute` | POST | Execute any shell command |
| `/v1/azure-vm/gpu-status` | GET | Check GPU with nvidia-smi |
| `/v1/azure-vm/system-resources` | GET | CPU, memory, disk, GPU info |
| `/v1/azure-vm/training-jobs` | GET | List running Python jobs |
| `/v1/azure-vm/start-training` | POST | Start training in background |
| `/v1/azure-vm/tail-log` | POST | View log file contents |
| `/v1/azure-vm/disk-usage` | GET | Check disk space |

---

## 📖 **Full Documentation**

See `AZURE_VM_SETUP.md` for complete API reference with examples.

---

**Status:** ✅ Ready to use  
**Server:** Running on port 5000  
**Auth:** All endpoints require API key (except health check)
