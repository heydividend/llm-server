# ML Scheduler Deployment Guide

## Quick Start 🚀

Deploy the new ML scheduler features to your Azure VM in 3 simple steps:

### Step 1: Deploy to Azure VM
```bash
bash deploy_ml_schedulers_to_azure.sh
```

### Step 2: Verify Deployment
```bash
# Without API key (tests public endpoints)
bash verify_ml_scheduler_deployment.sh

# With API key (full testing)
bash verify_ml_scheduler_deployment.sh YOUR_HARVEY_AI_API_KEY
```

### Step 3: Test New Endpoints
```bash
# Test scheduler health
curl http://20.81.210.213:8001/v1/ml-schedulers/health \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get payout ratings
curl -X POST http://20.81.210.213:8001/v1/ml-schedulers/payout-ratings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"symbols": ["AAPL", "MSFT", "JNJ"]}'
```

## What Gets Deployed 📦

### New Features:
- ✅ **ML Scheduler API Endpoints** (`/v1/ml-schedulers/*`)
- ✅ **Self-Healing System** with circuit breakers
- ✅ **Caching Layer** for fast responses
- ✅ **Admin Dashboard** for monitoring
- ✅ **Updated Documentation**

### New Files:
- `app/routes/ml_schedulers.py` - FastAPI routes
- `app/services/ml_schedulers_service.py` - Scheduler service
- `app/core/self_healing.py` - Self-healing system
- Updated `app/services/ml_api_client.py` - New methods
- Updated `app/services/ml_integration.py` - Integration layer
- Updated `main.py` - Route registration

## Schedule Reminders ⏰

Your ML schedulers run automatically on Azure VM:

| Scheduler | Schedule | What it Does |
|-----------|----------|--------------|
| **Payout Rating** | Daily 1:00 AM UTC | Grades all dividend stocks (A+ to F) |
| **Dividend Calendar** | Sunday 2:00 AM UTC | Predicts next payment dates |
| **ML Training** | Sunday 3:00 AM UTC | Retrains all ML models |

## Monitoring 📊

### Check Service Status
```bash
# SSH into Azure VM
ssh azureuser@20.81.210.213

# Check Harvey API
sudo systemctl status harvey

# Check scheduler timers
sudo systemctl status harvey-payout-rating.timer
sudo systemctl status harvey-dividend-calendar.timer
sudo systemctl status harvey-ml-training.timer

# View logs
sudo journalctl -u harvey -f
```

### Monitor Endpoints
```bash
# Health dashboard
curl http://20.81.210.213:8001/v1/ml-schedulers/health \
  -H "Authorization: Bearer YOUR_API_KEY"

# Admin dashboard
curl http://20.81.210.213:8001/v1/ml-schedulers/admin/dashboard \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY"
```

## Troubleshooting 🔧

### If deployment fails:

1. **Check SSH access:**
   ```bash
   ssh azureuser@20.81.210.213 echo "Connected"
   ```

2. **Check service logs:**
   ```bash
   ssh azureuser@20.81.210.213 'sudo journalctl -u harvey -n 50'
   ```

3. **Restart Harvey service:**
   ```bash
   ssh azureuser@20.81.210.213 'sudo systemctl restart harvey'
   ```

### Common Issues:

- **404 on new endpoints**: Run deployment script
- **401 Unauthorized**: Add API key to requests
- **500 errors**: Check service logs
- **Connection refused**: Ensure services are running

## Rollback 🔄

If you need to rollback:

```bash
# SSH into VM
ssh azureuser@20.81.210.213

# Restore from backup (backups are created during deployment)
cd /home/azureuser/harvey
cp -r backups/backup_YYYYMMDD_HHMMSS/* .

# Restart service
sudo systemctl restart harvey
```

## Success Indicators ✅

You'll know deployment succeeded when:

1. `/v1/ml-schedulers/health` returns 200 OK
2. Payout ratings return A+ to F grades
3. Dividend calendar shows predictions
4. Training status shows "completed"
5. Admin dashboard shows all "healthy"

## Next Steps 🎯

After successful deployment:

1. **Test all endpoints** with real data
2. **Monitor cache performance** via admin dashboard
3. **Check scheduler execution** after their scheduled times
4. **Review self-healing logs** for any auto-recoveries
5. **Update frontend** to use cached endpoints for speed

## Support 💬

- **Logs**: `/home/azureuser/harvey/logs/`
- **Backups**: `/home/azureuser/harvey/backups/`
- **Config**: Check environment variables in `.env`
- **Database**: Azure SQL Server connection

---

🎉 **Congratulations!** Your ML scheduler integration is ready for production!