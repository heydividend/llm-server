# Harvey AI - Data Scientist Agent Deployment Runbook

## Prerequisites

- SSH access to Azure VM (20.81.210.213)
- Harvey repository at `/home/azureuser/harvey`
- Environment variables configured in `/home/azureuser/.env`
- Python 3.11+ with required packages

---

## Deployment Steps

### 1. SSH to Azure VM

```bash
ssh azureuser@20.81.210.213
```

### 2. Navigate to Harvey Directory

```bash
cd /home/azureuser/harvey
```

### 3. Pull Latest Code (if using Git)

```bash
git pull origin main
```

*Or manually copy files if not using Git*

### 4. Verify Environment Variables

```bash
# Check required database credentials
grep -E "SQLSERVER_HOST|SQLSERVER_USER|SQLSERVER_PASSWORD|SQLSERVER_DB" .env

# Check Gemini API key (for recommendations)
grep "GEMINI_API_KEY" .env
```

**Required environment variables:**
- `SQLSERVER_HOST`
- `SQLSERVER_USER`  
- `SQLSERVER_PASSWORD`
- `SQLSERVER_DB`
- `GEMINI_API_KEY` (for AI recommendations)

### 5. Run Deployment Script

```bash
chmod +x azure_vm_setup/deploy_data_scientist_agent.sh
./azure_vm_setup/deploy_data_scientist_agent.sh
```

**Expected output:**
```
==================================================================
Harvey AI - Data Scientist Agent Deployment
==================================================================

📦 Creating directory structure...
📝 Deploying Data Scientist Agent Service...
✅ Service deployed: /home/azureuser/harvey/app/services/data_scientist_agent.py
📝 Deploying CLI Tool...
✅ CLI deployed: /home/azureuser/harvey/scripts/data_scientist_agent.py

==================================================================
✅ Data Scientist Agent Deployed Successfully!
==================================================================
```

---

## Post-Deployment Smoke Tests

### Test 1: Schema Analysis

```bash
cd /home/azureuser/harvey
python3 scripts/data_scientist_agent.py --schema-only
```

**Expected:** Should list all database tables and columns

### Test 2: Data Distribution

```bash
python3 scripts/data_scientist_agent.py --distribution-only
```

**Expected:** Should show row counts for all tables

### Test 3: Training Coverage

```bash
python3 scripts/data_scientist_agent.py --coverage-only
```

**Expected:** Should display question counts by category

### Test 4: Model Performance

```bash
python3 scripts/data_scientist_agent.py --performance-only
```

**Expected:** Should show comparison of all 5 AI models

### Test 5: Full Analysis with AI Recommendations

```bash
python3 scripts/data_scientist_agent.py --analyze --output /tmp/harvey_analysis.json
```

**Expected:** 
- Complete analysis with all 6 sections
- AI-generated recommendations using Gemini 2.0
- JSON report saved to `/tmp/harvey_analysis.json`

---

## Troubleshooting

### Database Connection Error

```bash
# Test database connectivity
python3 -c "
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(override=True)
host = os.getenv('SQLSERVER_HOST')
user = os.getenv('SQLSERVER_USER')
password = os.getenv('SQLSERVER_PASSWORD')
database = os.getenv('SQLSERVER_DB')

conn_str = f'mssql+pyodbc://{user}:{password}@{host}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes'
engine = create_engine(conn_str)

with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM training_questions'))
    count = result.scalar()
    print(f'✅ Database connected! Training questions: {count}')
"
```

### Missing Dependencies

```bash
# Install required packages
pip3 install sqlalchemy pyodbc python-dotenv google-generativeai
```

### ODBC Driver Not Found

```bash
# Install ODBC Driver 18
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Gemini API Error

```bash
# Verify API key format (should be 39 characters starting with "AIzaSy")
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv(override=True)
key = os.getenv('GEMINI_API_KEY')
print(f'API Key: {\"Valid\" if key and len(key) == 39 and key.startswith(\"AIzaSy\") else \"INVALID\"}')'
"
```

---

## Optional: Schedule Monthly Analysis

Add to crontab for automated monthly reports:

```bash
crontab -e
```

Add this line:

```bash
# Run Data Scientist Agent on 1st of each month at 5:00 AM
0 5 1 * * cd /home/azureuser/harvey && /usr/bin/python3 scripts/data_scientist_agent.py --analyze --output /var/log/harvey/monthly_analysis_$(date +\%Y\%m).json >> /var/log/harvey/data_scientist_agent.log 2>&1
```

---

## Files Deployed

1. **Service:** `/home/azureuser/harvey/app/services/data_scientist_agent.py`
   - Core analysis engine
   - Database connectivity
   - Gemini 2.0 integration

2. **CLI Tool:** `/home/azureuser/harvey/scripts/data_scientist_agent.py`
   - Command-line interface
   - Formatted output
   - JSON export

---

## Quick Reference

```bash
# Full analysis
python3 scripts/data_scientist_agent.py --analyze

# Individual analyses
python3 scripts/data_scientist_agent.py --schema-only
python3 scripts/data_scientist_agent.py --distribution-only
python3 scripts/data_scientist_agent.py --coverage-only
python3 scripts/data_scientist_agent.py --performance-only
python3 scripts/data_scientist_agent.py --feedback-only
python3 scripts/data_scientist_agent.py --recommendations-only

# Save report
python3 scripts/data_scientist_agent.py --analyze --output report.json

# Quiet mode (for cron jobs)
python3 scripts/data_scientist_agent.py --analyze --quiet --output report.json
```

---

## Support

- **Documentation:** `/home/azureuser/harvey/docs/DATA_SCIENTIST_AGENT.md`
- **Logs:** Check stdout/stderr or redirect to `/var/log/harvey/`
- **Issues:** Review error messages for specific guidance

---

**Deployment Date:** November 20, 2025  
**Version:** 1.0.0  
**Status:** Ready for Production ✅
