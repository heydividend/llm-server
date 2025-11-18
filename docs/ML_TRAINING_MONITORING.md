# Harvey ML Training System - Monitoring Guide

## Overview

This guide covers how to monitor and verify the ML training system running on the Azure VM.

## ML Training Infrastructure

### Services Running

**1. heydividend-ml-schedulers.service**
- **Purpose**: Automated ML training orchestration
- **Location**: `/home/azureuser/ml-api/main-ml.py`
- **Status Check**: `sudo systemctl status heydividend-ml-schedulers`

**2. harvey-ml.service**
- **Purpose**: Harvey Intelligence Engine (ML inference API)
- **Port**: 9001
- **Endpoints**: 22+ ML prediction endpoints
- **Status Check**: `sudo systemctl status harvey-ml`

**3. harvey-backend.service**
- **Purpose**: Main Harvey API (uses ML service)
- **Port**: 8001
- **Status Check**: `sudo systemctl status harvey-backend`

---

## Training Schedule

### Daily Jobs

**Payout Rating ML**
- **Time**: 1:00 AM UTC daily
- **Purpose**: Generate A+/A/B/C dividend safety ratings
- **Database**: Writes to `payout_ratings` table
- **Models**: Payout sustainability and risk analysis

### Weekly Jobs (Sunday)

**Dividend Calendar ML**
- **Time**: 2:00 AM UTC Sunday
- **Purpose**: Predict next dividend payment dates
- **Database**: Writes to `dividend_calendar_predictions` table

**Full ML Model Training**
- **Time**: 3:00 AM UTC Sunday
- **Purpose**: Trains all 5 core ML models
- **Models**:
  - Dividend predictions
  - Payout ratings
  - Yield forecasting
  - Growth analysis
  - Cut risk detection
- **Location**: `/home/azureuser/ml-api/server/ml/training/`

---

## Monitoring Tools

### 1. Automated Training Report (Recommended)

Run the comprehensive training report script:

```bash
# On Azure VM
cd ~/harvey
python3 ml_training_report.py
```

**This script provides:**
- ✅ Service status for all Harvey services
- ✅ ML scheduler activity (last 7 days)
- ✅ Recent training job execution logs
- ✅ ML service health check
- ✅ Database prediction counts
- ✅ Next scheduled run times
- ✅ Training files and models status
- ✅ Actionable recommendations

**Example output:**
```
🎯 HARVEY ML TRAINING SYSTEM REPORT
Generated: 2025-11-17 23:30:00 UTC
Hostname: llm-training-vm

🔧 SERVICE STATUS
✅ Harvey Backend API (port 8001)
   Status: RUNNING
   Started: Mon 2025-11-17 23:26:38 UTC

✅ ML Intelligence Engine (port 9001)
   Status: RUNNING
   Started: Mon 2025-11-17 23:20:47 UTC

✅ ML Training Schedulers
   Status: RUNNING
   Started: Mon 2025-11-17 23:20:47 UTC
```

---

### 2. Manual Log Inspection

**Check scheduler logs (last 24 hours):**
```bash
sudo journalctl -u heydividend-ml-schedulers --since "24 hours ago" --no-pager
```

**Check scheduler logs (last 7 days):**
```bash
sudo journalctl -u heydividend-ml-schedulers --since "7 days ago" --no-pager | less
```

**Check if Sunday training ran:**
```bash
sudo journalctl -u heydividend-ml-schedulers --since "2025-11-17 03:00" --until "2025-11-17 04:00"
```

**Check if daily payout rating ran:**
```bash
sudo journalctl -u heydividend-ml-schedulers --since "yesterday 01:00" --until "yesterday 02:00"
```

**Follow logs in real-time:**
```bash
sudo journalctl -u heydividend-ml-schedulers -f
```

---

### 3. Service Health Checks

**Check all services:**
```bash
sudo systemctl status harvey-backend harvey-ml heydividend-ml-schedulers nginx
```

**Check ML service health endpoint:**
```bash
curl http://localhost:9001/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "harvey-intelligence-engine",
  "version": "2.0.0"
}
```

**Check if services are listening on ports:**
```bash
ss -ltnp | grep -E "8001|9001"
```

---

### 4. Database Verification

**Connect to database:**
```bash
sqlcmd -S $SQLSERVER_HOST -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -d $SQLSERVER_DB
```

**Check recent payout ratings:**
```sql
SELECT COUNT(*) 
FROM payout_ratings 
WHERE created_at > DATEADD(day, -7, GETDATE());
GO
```

**Check recent dividend calendar predictions:**
```sql
SELECT COUNT(*) 
FROM dividend_calendar_predictions 
WHERE created_at > DATEADD(day, -7, GETDATE());
GO
```

**Check latest ML predictions:**
```sql
SELECT TOP 10 ticker, rating, created_at 
FROM payout_ratings 
ORDER BY created_at DESC;
GO
```

---

### 5. Training Files & Models

**Check training scripts:**
```bash
ls -la /home/azureuser/ml-api/server/ml/training/
```

**Check model files:**
```bash
ls -lth /home/azureuser/ml-api/models/ | head -20
```

**Check when models were last modified:**
```bash
find /home/azureuser/ml-api/models/ -type f -mtime -7 -exec ls -lh {} \;
```

---

## Troubleshooting

### Problem: Scheduler service not running

**Diagnosis:**
```bash
sudo systemctl status heydividend-ml-schedulers
```

**Fix:**
```bash
sudo systemctl restart heydividend-ml-schedulers
sudo systemctl status heydividend-ml-schedulers
```

**Check logs for errors:**
```bash
sudo journalctl -u heydividend-ml-schedulers -n 100
```

---

### Problem: Training jobs not executing

**Check scheduler configuration:**
```bash
cat /etc/systemd/system/heydividend-ml-schedulers.service
```

**Manually trigger training (for testing):**
```bash
cd /home/azureuser/ml-api
source venv/bin/activate
python3 main-ml.py
```

**Check if Python dependencies are installed:**
```bash
cd /home/azureuser/ml-api
source venv/bin/activate
pip list | grep -E "torch|sklearn|pandas|numpy"
```

---

### Problem: ML service not responding

**Check if port 9001 is listening:**
```bash
ss -ltnp | grep 9001
```

**Restart ML service:**
```bash
sudo systemctl restart harvey-ml
sudo systemctl status harvey-ml
```

**Check ML service logs:**
```bash
sudo journalctl -u harvey-ml -n 100
```

---

### Problem: Database connection failures

**Check database connectivity:**
```bash
sqlcmd -S $SQLSERVER_HOST -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -d $SQLSERVER_DB -Q "SELECT @@VERSION"
```

**Check environment variables:**
```bash
echo $SQLSERVER_HOST
echo $SQLSERVER_USER
echo $SQLSERVER_DB
```

**Verify credentials in service file:**
```bash
sudo systemctl cat heydividend-ml-schedulers | grep Environment
```

---

## Performance Metrics

### Expected Training Times

| Job | Duration | Frequency |
|-----|----------|-----------|
| Payout Rating ML | ~5-15 minutes | Daily (1:00 AM) |
| Dividend Calendar ML | ~3-10 minutes | Weekly (Sunday 2:00 AM) |
| Full Model Training | ~30-60 minutes | Weekly (Sunday 3:00 AM) |

### Database Growth

| Table | Expected Growth | Retention |
|-------|----------------|-----------|
| payout_ratings | ~100-500 records/day | 90 days |
| dividend_calendar_predictions | ~200-1000 records/week | 90 days |
| ml_model_metadata | ~5 records/week | Indefinite |

---

## Maintenance Tasks

### Weekly Checks (Recommended)

```bash
# Run automated report
cd ~/harvey
python3 ml_training_report.py > /tmp/ml_report_$(date +%Y%m%d).txt

# Review the report
less /tmp/ml_report_$(date +%Y%m%d).txt
```

### Monthly Checks

1. **Verify model files are being updated:**
   ```bash
   ls -lth /home/azureuser/ml-api/models/ | head -20
   ```

2. **Check disk space:**
   ```bash
   df -h
   ```

3. **Review database size:**
   ```sql
   EXEC sp_spaceused;
   GO
   ```

4. **Check for failed jobs:**
   ```bash
   sudo journalctl -u heydividend-ml-schedulers --since "30 days ago" | grep -i "error\|failed" | wc -l
   ```

---

## Quick Reference Commands

```bash
# Service management
sudo systemctl status heydividend-ml-schedulers
sudo systemctl restart heydividend-ml-schedulers
sudo systemctl stop heydividend-ml-schedulers
sudo systemctl start heydividend-ml-schedulers

# View logs
sudo journalctl -u heydividend-ml-schedulers -f                    # Follow logs
sudo journalctl -u heydividend-ml-schedulers --since "1 hour ago"  # Last hour
sudo journalctl -u heydividend-ml-schedulers -n 100                # Last 100 lines

# Health checks
curl http://localhost:9001/health          # ML service
curl http://localhost:8001/health          # Harvey backend
systemctl is-active heydividend-ml-schedulers  # Quick status

# Generate report
cd ~/harvey && python3 ml_training_report.py
```

---

## Automated Monitoring (Optional)

### Create a cron job to run daily reports:

```bash
# Edit crontab
crontab -e

# Add this line to run report daily at 9:00 AM
0 9 * * * cd /home/azureuser/harvey && python3 ml_training_report.py > /tmp/ml_report_$(date +\%Y\%m\%d).txt 2>&1
```

### Email alerts on failures (requires sendmail):

```bash
# Add to cron
0 1 * * * systemctl is-active heydividend-ml-schedulers || echo "ML Scheduler is down!" | mail -s "Alert: ML Training Service Down" your@email.com
```

---

## Contact & Support

For issues with the ML training system:
1. Run `ml_training_report.py` and save the output
2. Check recent logs: `sudo journalctl -u heydividend-ml-schedulers -n 200`
3. Document the issue with timestamps and error messages
4. Contact the Harvey AI development team

---

**Last Updated**: November 17, 2025  
**Version**: Harvey ML Training v2.0
