#!/usr/bin/env python3
"""
Harvey ML Training Report Generator
Generates a detailed report of ML training activity, job execution, and system health.
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
import json

def run_command(cmd):
    """Execute shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def check_service_status():
    """Check status of all Harvey services"""
    print("=" * 80)
    print("🔧 SERVICE STATUS")
    print("=" * 80)
    
    services = [
        ("harvey-backend", "Harvey Backend API (port 8001)"),
        ("harvey-ml", "ML Intelligence Engine (port 9001)"),
        ("heydividend-ml-schedulers", "ML Training Schedulers"),
        ("nginx", "Nginx Reverse Proxy")
    ]
    
    for service_name, description in services:
        status = run_command(f"systemctl is-active {service_name}")
        uptime = run_command(f"systemctl show {service_name} --property=ActiveEnterTimestamp --value")
        
        if status == "active":
            print(f"✅ {description}")
            print(f"   Service: {service_name}")
            print(f"   Status: RUNNING")
            print(f"   Started: {uptime}")
        else:
            print(f"❌ {description}")
            print(f"   Service: {service_name}")
            print(f"   Status: {status.upper()}")
        print()

def analyze_scheduler_logs():
    """Analyze heydividend-ml-schedulers logs for training activity"""
    print("=" * 80)
    print("🤖 ML SCHEDULER ACTIVITY (Last 7 Days)")
    print("=" * 80)
    
    # Get logs from last 7 days
    logs = run_command('sudo journalctl -u heydividend-ml-schedulers --since "7 days ago" --no-pager')
    
    if "Error" in logs or not logs:
        print("❌ Unable to retrieve scheduler logs")
        print(f"   {logs}")
        return
    
    # Count key events
    lines = logs.split('\n')
    
    events = {
        'payout_rating': {'keywords': ['payout rating', 'payout_rating', 'rating ml'], 'count': 0, 'last_seen': None},
        'dividend_calendar': {'keywords': ['dividend calendar', 'calendar ml', 'calendar prediction'], 'count': 0, 'last_seen': None},
        'model_training': {'keywords': ['model training', 'training ml', 'train model', 'training all'], 'count': 0, 'last_seen': None},
        'errors': {'keywords': ['error', 'exception', 'failed', 'traceback'], 'count': 0, 'last_seen': None},
        'success': {'keywords': ['success', 'completed', 'finished'], 'count': 0, 'last_seen': None}
    }
    
    for line in lines:
        line_lower = line.lower()
        
        # Extract timestamp if present
        timestamp = None
        if line.startswith(('Nov ', 'Dec ', 'Jan ', 'Feb ')):
            try:
                timestamp = ' '.join(line.split()[:3])
            except:
                pass
        
        for event_name, event_data in events.items():
            for keyword in event_data['keywords']:
                if keyword in line_lower:
                    event_data['count'] += 1
                    if timestamp and not event_data['last_seen']:
                        event_data['last_seen'] = timestamp
                    break
    
    # Print summary
    print("\n📊 Event Summary:")
    print(f"   Payout Rating ML runs: {events['payout_rating']['count']} events")
    if events['payout_rating']['last_seen']:
        print(f"      Last seen: {events['payout_rating']['last_seen']}")
    
    print(f"   Dividend Calendar runs: {events['dividend_calendar']['count']} events")
    if events['dividend_calendar']['last_seen']:
        print(f"      Last seen: {events['dividend_calendar']['last_seen']}")
    
    print(f"   Model Training runs: {events['model_training']['count']} events")
    if events['model_training']['last_seen']:
        print(f"      Last seen: {events['model_training']['last_seen']}")
    
    print(f"   Success events: {events['success']['count']}")
    print(f"   Error events: {events['errors']['count']}")
    
    if events['errors']['count'] > 0:
        print(f"      ⚠️  {events['errors']['count']} errors detected in logs")
    
    print()

def check_recent_scheduler_logs():
    """Check last 24 hours of scheduler activity"""
    print("=" * 80)
    print("📅 RECENT SCHEDULER ACTIVITY (Last 24 Hours)")
    print("=" * 80)
    
    logs = run_command('sudo journalctl -u heydividend-ml-schedulers --since "24 hours ago" --no-pager | tail -50')
    
    if logs and "Error" not in logs:
        print(logs)
    else:
        print("No recent activity or unable to retrieve logs")
    print()

def check_ml_service_health():
    """Check ML service health endpoint"""
    print("=" * 80)
    print("🏥 ML SERVICE HEALTH CHECK")
    print("=" * 80)
    
    # Check if port 9001 is listening
    port_check = run_command("ss -ltnp | grep ':9001'")
    
    if port_check:
        print("✅ ML Service is listening on port 9001")
        print(f"   {port_check}")
        
        # Try to hit health endpoint
        health = run_command("curl -s http://localhost:9001/health 2>/dev/null")
        if health and "{" in health:
            print("\n✅ ML Service Health Response:")
            try:
                import json
                health_data = json.loads(health)
                for key, value in health_data.items():
                    print(f"   {key}: {value}")
            except:
                print(f"   {health}")
        else:
            print("❌ Unable to reach health endpoint")
    else:
        print("❌ ML Service not listening on port 9001")
    
    print()

def check_database_predictions():
    """Check database for recent ML predictions"""
    print("=" * 80)
    print("💾 DATABASE PREDICTIONS CHECK")
    print("=" * 80)
    
    # Check if sqlcmd is available
    sqlcmd_check = run_command("which sqlcmd")
    
    if not sqlcmd_check or "not found" in sqlcmd_check:
        print("⚠️  sqlcmd not available - skipping database checks")
        print("   Install with: sudo apt-get install mssql-tools")
        print()
        return
    
    # Get database connection info from environment
    db_host = os.getenv('SQLSERVER_HOST')
    db_user = os.getenv('SQLSERVER_USER')
    db_pass = os.getenv('SQLSERVER_PASSWORD')
    db_name = os.getenv('SQLSERVER_DB')
    
    if not all([db_host, db_user, db_pass, db_name]):
        print("⚠️  Database credentials not found in environment")
        print()
        return
    
    # Check for recent payout ratings
    print("Checking recent ML predictions...")
    
    tables_to_check = [
        ("payout_ratings", "Payout Rating Predictions"),
        ("dividend_calendar_predictions", "Dividend Calendar Predictions"),
        ("ml_model_metadata", "ML Model Metadata")
    ]
    
    for table_name, description in tables_to_check:
        query = f"SELECT COUNT(*) as count FROM {table_name} WHERE created_at > DATEADD(day, -7, GETDATE());"
        cmd = f"sqlcmd -S {db_host} -U {db_user} -P '{db_pass}' -d {db_name} -Q \"{query}\" -h -1 -W 2>/dev/null"
        
        result = run_command(cmd)
        
        if result and result.isdigit():
            count = int(result)
            if count > 0:
                print(f"✅ {description}: {count} records (last 7 days)")
            else:
                print(f"⚠️  {description}: No recent records")
        else:
            print(f"❓ {description}: Unable to query")
    
    print()

def check_training_schedule():
    """Display expected training schedule"""
    print("=" * 80)
    print("📅 TRAINING SCHEDULE")
    print("=" * 80)
    
    now = datetime.now()
    
    print("\n🕐 Scheduled Jobs:")
    print("   1. Payout Rating ML")
    print("      Schedule: Daily at 1:00 AM UTC")
    print("      Purpose: Generate A+/A/B/C dividend safety ratings")
    
    print("\n   2. Dividend Calendar ML")
    print("      Schedule: Sunday at 2:00 AM UTC")
    print("      Purpose: Predict next dividend payment dates")
    
    print("\n   3. Full ML Model Training")
    print("      Schedule: Sunday at 3:00 AM UTC")
    print("      Purpose: Train all 5 core ML models")
    print("      Models: Dividend predictions, payout ratings, yield forecasting,")
    print("              growth analysis, cut risk detection")
    
    # Calculate next run times
    print("\n📆 Next Scheduled Runs:")
    
    # Next 1:00 AM (Payout Rating)
    next_1am = now.replace(hour=1, minute=0, second=0, microsecond=0)
    if now.hour >= 1:
        next_1am += timedelta(days=1)
    print(f"   Next Payout Rating ML: {next_1am.strftime('%Y-%m-%d %H:%M UTC')} ({(next_1am - now).total_seconds() / 3600:.1f} hours)")
    
    # Next Sunday 2:00 AM (Dividend Calendar)
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.hour >= 2:
        days_until_sunday = 7
    next_sunday_2am = (now + timedelta(days=days_until_sunday)).replace(hour=2, minute=0, second=0, microsecond=0)
    print(f"   Next Dividend Calendar ML: {next_sunday_2am.strftime('%Y-%m-%d %H:%M UTC')} ({(next_sunday_2am - now).total_seconds() / 3600:.1f} hours)")
    
    # Next Sunday 3:00 AM (Model Training)
    next_sunday_3am = next_sunday_2am.replace(hour=3)
    print(f"   Next Model Training: {next_sunday_3am.strftime('%Y-%m-%d %H:%M UTC')} ({(next_sunday_3am - now).total_seconds() / 3600:.1f} hours)")
    
    print()

def check_training_files():
    """Check for training script files"""
    print("=" * 80)
    print("📁 TRAINING SCRIPTS & MODELS")
    print("=" * 80)
    
    paths_to_check = [
        ("/home/azureuser/harvey/server/ml/training", "Training Scripts"),
        ("/home/azureuser/ml-api/server/ml/training", "ML API Training Scripts"),
        ("/home/azureuser/harvey/models", "Harvey Models"),
        ("/home/azureuser/ml-api/models", "ML API Models"),
    ]
    
    for path, description in paths_to_check:
        if os.path.exists(path):
            file_count = run_command(f"find {path} -type f | wc -l")
            last_modified = run_command(f"ls -lt {path} | head -5")
            print(f"✅ {description}")
            print(f"   Path: {path}")
            print(f"   Files: {file_count}")
            if last_modified:
                print(f"   Recent files:")
                for line in last_modified.split('\n')[1:4]:
                    if line.strip():
                        print(f"      {line}")
        else:
            print(f"❌ {description}")
            print(f"   Path not found: {path}")
        print()

def generate_recommendations():
    """Generate recommendations based on findings"""
    print("=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n✅ Manual Verification Steps:")
    print("   1. Check if training ran last Sunday (3:00 AM):")
    print("      sudo journalctl -u heydividend-ml-schedulers --since '2025-11-17 03:00' --until '2025-11-17 04:00'")
    
    print("\n   2. Check daily payout rating runs:")
    print("      sudo journalctl -u heydividend-ml-schedulers --since 'yesterday 01:00' --until 'yesterday 02:00'")
    
    print("\n   3. Monitor next scheduled run in real-time:")
    print("      sudo journalctl -u heydividend-ml-schedulers -f")
    
    print("\n   4. Manually trigger a training run (testing):")
    print("      cd /home/azureuser/ml-api && python3 main-ml.py")
    
    print("\n   5. Check database for recent predictions:")
    print("      sqlcmd -S $SQLSERVER_HOST -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -d $SQLSERVER_DB")
    print("      Then run: SELECT COUNT(*) FROM payout_ratings WHERE created_at > DATEADD(day, -7, GETDATE());")
    
    print()

def main():
    """Main report generator"""
    print("\n")
    print("=" * 80)
    print("🎯 HARVEY ML TRAINING SYSTEM REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Hostname: {run_command('hostname')}")
    print("=" * 80)
    print("\n")
    
    # Run all checks
    check_service_status()
    check_ml_service_health()
    check_training_schedule()
    analyze_scheduler_logs()
    check_recent_scheduler_logs()
    check_database_predictions()
    check_training_files()
    generate_recommendations()
    
    print("=" * 80)
    print("✅ Report Complete")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
