# Harvey - Azure VM Deployment Guide

## Deployment Architecture

Harvey is deployed to **Azure VM**, not to Replit's infrastructure. Replit is used only for development.

```
┌─────────────────────────────────────────────────────┐
│                   Azure VM (Ubuntu)                  │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │         Nginx (Port 80/443)                 │    │
│  │         Reverse Proxy                       │    │
│  └─────────────┬────────────────┬──────────────┘    │
│                │                │                    │
│  ┌─────────────▼──────┐  ┌──────▼─────────────┐    │
│  │  Harvey Backend    │  │   ML Prediction    │    │
│  │   (FastAPI)        │  │      API           │    │
│  │   Port 8000        │  │   Port 9000        │    │
│  └────────────────────┘  └────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
            ┌──────────────────────┐
            │  Azure SQL Server    │
            │  (HeyDividend DB)    │
            └──────────────────────┘
```

---

## Quick Deploy (5 Minutes)

### Step 1: Prepare Deployment Script

1. Open `deploy/AZURE_RUN_COMMAND_DEPLOY.sh`
2. Edit the secrets section (lines 18-25):

```bash
HARVEY_AI_API_KEY="your-actual-api-key"
SQLSERVER_HOST="your-server.database.windows.net"
SQLSERVER_DB="HeyDividend"
SQLSERVER_USER="your-username"
SQLSERVER_PASSWORD="your-password"
OPENAI_API_KEY="sk-..."
INTERNAL_ML_API_KEY="your-ml-api-key"
PDFCO_API_KEY="your-pdfco-key"
```

### Step 2: Deploy via Azure Portal

1. Go to Azure Portal → Your VM → **Run Command**
2. Select **RunShellScript**
3. Paste entire contents of `deploy/AZURE_RUN_COMMAND_DEPLOY.sh`
4. Click **Run**

**Wait 3-5 minutes** for deployment to complete.

### Step 3: Verify Deployment

```bash
# Check Harvey backend
curl http://your-vm-ip/health

# Check ML API
curl http://your-vm-ip/ml/health

# Check feedback system
curl http://your-vm-ip/v1/feedback/summary
```

---

## What Gets Deployed

### Harvey Backend (Port 8000)
- FastAPI server
- All routes (chat, feedback, tax, alerts, insights, etc.)
- Background scheduler (alerts, digests)
- Conversation memory system
- Feedback collection system

### ML Prediction API (Port 9000)
- 22+ ML endpoints
- Model serving from Azure Blob Storage
- Prediction caching
- Health monitoring

### Nginx Configuration
- Reverse proxy to both services
- SSL/TLS termination (if configured)
- Rate limiting
- Static file serving

### System Services
- `harvey-backend.service` - Harvey FastAPI server
- `ml-api.service` - ML prediction API
- `nginx.service` - Reverse proxy

---

## Deployment Options

### Option 1: Azure Run Command (Recommended)
**No SSH required! No file uploads!**

- Run script via Azure Portal → VM → Run Command
- Automatically pulls latest code from Replit
- Configures everything in one step

### Option 2: SSH Deployment
```bash
# SSH into Azure VM
ssh azureuser@your-vm-ip

# Clone Harvey backend
git clone https://github.com/your-org/harvey-backend.git
cd harvey-backend

# Run deployment script
sudo bash deploy/local_deploy.sh
```

### Option 3: GitHub Actions (Future)
Automated CI/CD pipeline (not yet implemented)

---

## Updating Feedback System

After deploying the feedback system to Azure VM:

### 1. Create Feedback Tables

SSH into your Azure VM and run:

```bash
# Connect to Azure SQL from the VM
sqlcmd -S $SQLSERVER_HOST -d $SQLSERVER_DB -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -i /opt/harvey-backend/app/database/feedback_schema.sql
```

Or run via Azure Portal Query Editor (copy/paste the schema).

### 2. Restart Harvey Backend

```bash
sudo systemctl restart harvey-backend
```

### 3. Verify Feedback System

```bash
# Test feedback endpoint
curl -X POST http://your-vm-ip/v1/feedback/test123/positive

# View dashboard
curl http://your-vm-ip/v1/feedback/analytics/dashboard
```

---

## Environment Variables

Harvey backend requires these environment variables (set by deployment script):

```bash
# API Authentication
HARVEY_AI_API_KEY="your-api-key"

# Database
SQLSERVER_HOST="server.database.windows.net"
SQLSERVER_DB="HeyDividend"
SQLSERVER_USER="username"
SQLSERVER_PASSWORD="password"

# AI Models
OPENAI_API_KEY="sk-..."

# ML API
INTERNAL_ML_API_KEY="ml-api-key"
ML_API_BASE_URL="http://localhost:9000/api/internal/ml"

# Document Processing
PDFCO_API_KEY="pdfco-key"
```

---

## Monitoring & Logs

### View Harvey Backend Logs
```bash
sudo journalctl -u harvey-backend -f
```

### View ML API Logs
```bash
sudo journalctl -u ml-api -f
```

### View Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Service Status
```bash
sudo systemctl status harvey-backend
sudo systemctl status ml-api
sudo systemctl status nginx
```

---

## Nginx Configuration

Harvey backend is proxied through Nginx:

```nginx
# /etc/nginx/sites-available/harvey

upstream harvey_backend {
    server localhost:8000;
}

upstream ml_api {
    server localhost:9000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Harvey backend
    location / {
        proxy_pass http://harvey_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # ML API
    location /ml/ {
        proxy_pass http://ml_api/;
        proxy_set_header Host $host;
    }

    # Feedback endpoints
    location /v1/feedback/ {
        proxy_pass http://harvey_backend/v1/feedback/;
    }
}
```

---

## Troubleshooting

### "Connection refused" errors
```bash
# Check if services are running
sudo systemctl status harvey-backend
sudo systemctl status ml-api

# Restart if needed
sudo systemctl restart harvey-backend
sudo systemctl restart ml-api
```

### Database connection errors
```bash
# Test database connectivity
sqlcmd -S $SQLSERVER_HOST -d $SQLSERVER_DB -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -Q "SELECT 1"
```

### Feedback tables not found
```bash
# Run feedback schema
sqlcmd -S $SQLSERVER_HOST -d $SQLSERVER_DB -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -i /opt/harvey-backend/app/database/feedback_schema.sql
```

### ML API unreachable
```bash
# Check ML API health
curl http://localhost:9000/health

# Check Azure NSG rules (port 9000 should be allowed internally)
```

---

## Replit vs Azure VM

| Aspect | Replit (Development) | Azure VM (Production) |
|--------|---------------------|----------------------|
| **Purpose** | Development & testing | Production deployment |
| **Environment** | NixOS | Ubuntu Linux |
| **Port** | 5000 (webview) | 80/443 (Nginx) |
| **Database** | Azure SQL Server | Azure SQL Server |
| **ML API** | Remote (Azure VM) | Local (same VM) |
| **Deployment** | Automatic on save | Manual via script |
| **Cost** | Replit subscription | Azure VM pricing |

---

## Production Checklist

Before deploying to production:

- [ ] All environment variables configured
- [ ] Database schema deployed (including feedback tables)
- [ ] SSL/TLS certificate configured in Nginx
- [ ] Firewall rules configured (NSG)
- [ ] Monitoring alerts set up
- [ ] Backup strategy configured
- [ ] Domain name configured
- [ ] API rate limiting enabled
- [ ] Log rotation configured

---

## Future Enhancements

### Planned Infrastructure Improvements

1. **Docker Containerization**
   - Package Harvey backend as Docker container
   - Package ML API as Docker container
   - Use Docker Compose for orchestration

2. **Kubernetes Deployment**
   - Deploy to Azure Kubernetes Service (AKS)
   - Auto-scaling based on load
   - Rolling updates with zero downtime

3. **CI/CD Pipeline**
   - GitHub Actions for automated testing
   - Automated deployment on merge to main
   - Blue-green deployments

4. **Multi-Region Deployment**
   - Deploy to multiple Azure regions
   - Azure Front Door for load balancing
   - Geographic traffic routing

---

## Support

For deployment issues:
1. Check logs: `sudo journalctl -u harvey-backend -f`
2. Verify services: `sudo systemctl status harvey-backend`
3. Test endpoints: `curl http://localhost:8000/health`
4. Review Azure NSG rules in Azure Portal

**Deployment script:** `deploy/AZURE_RUN_COMMAND_DEPLOY.sh`  
**Deployment model:** Azure VM (production), Replit (development)
