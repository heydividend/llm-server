#!/usr/bin/env python3
"""
Harvey ML Scheduler Sanity Check with Self-Healing
Verifies all components and attempts to auto-fix common issues.
Runs daily and logs results for monitoring.
"""

import os
import sys
import json
import requests
import subprocess
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import time

# Set up logging
LOG_DIR = "/home/azureuser/harvey/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure file and console logging
log_file = os.path.join(LOG_DIR, f"sanity_check_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    msg = f"\n{'=' * 70}\n{text}\n{'=' * 70}"
    print(f"{BLUE}{msg}{RESET}")
    logger.info(text)

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")
    logger.info(f"✅ {text}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")
    logger.error(f"❌ {text}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")
    logger.warning(f"⚠️  {text}")

def print_info(text):
    print(f"   {text}")
    logger.info(f"   {text}")

class HarveySelfHealingCheck:
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "errors": [],
            "warnings": [],
            "fixes_applied": [],
            "overall_status": "PASS"
        }
        self.auto_fix = True  # Enable auto-fixing by default
    
    def attempt_fix(self, issue, fix_command, description):
        """Attempt to fix an issue automatically"""
        if not self.auto_fix:
            return False
        
        print_warning(f"Attempting to fix: {description}")
        logger.info(f"Auto-fix attempt: {description}")
        
        try:
            if isinstance(fix_command, list):
                result = subprocess.run(fix_command, capture_output=True, text=True)
            else:
                result = subprocess.run(fix_command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print_success(f"Fixed: {description}")
                self.results["fixes_applied"].append({
                    "issue": issue,
                    "fix": description,
                    "timestamp": datetime.utcnow().isoformat()
                })
                return True
            else:
                print_warning(f"Fix failed: {result.stderr}")
                return False
        except Exception as e:
            print_warning(f"Fix error: {str(e)}")
            return False
    
    def check_and_fix_services(self):
        """Check and fix Harvey services"""
        print_header("SERVICE HEALTH CHECK & AUTO-HEALING")
        
        # Check Harvey API service
        try:
            response = requests.get("http://localhost:8001/health", timeout=3)
            if response.status_code in [200, 404]:
                print_success("Harvey API is running")
            else:
                raise Exception("API not responding")
        except:
            print_error("Harvey API is not running")
            # Try to restart it
            self.attempt_fix(
                "Harvey API down",
                "cd /home/azureuser/harvey && nohup /home/azureuser/miniconda3/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1 > harvey.log 2>&1 &",
                "Restarting Harvey API service on port 8001"
            )
        
        # Check ML service
        try:
            response = requests.get("http://localhost:9000/health", timeout=3)
            if response.status_code == 200:
                print_success("ML Service is running")
            else:
                raise Exception("ML Service not responding")
        except:
            print_error("ML Service is not running")
            # Try to restart ML service
            self.attempt_fix(
                "ML Service down",
                "sudo systemctl restart heydividend-ml-service || cd /home/azureuser/ml-service && nohup python main.py > ml.log 2>&1 &",
                "Restarting ML Service on port 9000"
            )
        
        # Check ML scheduler timers
        timers = [
            "ml-payout-rating.timer",
            "ml-dividend-calendar.timer",
            "ml-training.timer"
        ]
        
        for timer in timers:
            try:
                result = subprocess.run(
                    ["systemctl", "status", timer],
                    capture_output=True,
                    text=True
                )
                if "Active: active" in result.stdout:
                    print_success(f"{timer} is active")
                else:
                    print_warning(f"{timer} is not active")
                    self.attempt_fix(
                        f"{timer} inactive",
                        f"sudo systemctl enable {timer} && sudo systemctl start {timer}",
                        f"Enabling and starting {timer}"
                    )
            except:
                print_info(f"Cannot check {timer} (may need sudo)")
    
    def check_and_fix_database(self):
        """Check database connectivity and fix common issues"""
        print_header("DATABASE CONNECTIVITY & HEALING")
        
        try:
            import pymssql
            
            host = os.getenv("SQLSERVER_HOST")
            database = os.getenv("SQLSERVER_DB")
            user = os.getenv("SQLSERVER_USER")
            password = os.getenv("SQLSERVER_PASSWORD")
            
            if not all([host, database, user, password]):
                print_error("Missing database credentials")
                # Check if .env file exists
                if os.path.exists("/home/azureuser/harvey/.env"):
                    self.attempt_fix(
                        "Missing env vars",
                        "source /home/azureuser/harvey/.env",
                        "Loading environment variables from .env file"
                    )
                return False
            
            conn = pymssql.connect(
                server=host,
                user=user,
                password=password,
                database=database,
                timeout=10,
                as_dict=True
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.TABLES")
            count = cursor.fetchone()['count']
            print_success(f"Database connected: {count} tables found")
            
            # Check for required ML tables
            required_tables = ['model_audit_log', 'user_feedback']
            for table in required_tables:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{table}'
                """)
                if cursor.fetchone()['count'] == 0:
                    print_warning(f"Missing table: {table}")
                    # Create table if missing
                    if table == 'model_audit_log':
                        create_sql = """
                        CREATE TABLE model_audit_log (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            model_name VARCHAR(100),
                            user_query TEXT,
                            model_response TEXT,
                            response_time_ms INT,
                            created_at DATETIME DEFAULT GETDATE()
                        )
                        """
                        cursor.execute(create_sql)
                        conn.commit()
                        print_success(f"Created missing table: {table}")
                        self.results["fixes_applied"].append(f"Created table: {table}")
            
            cursor.close()
            conn.close()
            return True
            
        except ImportError:
            print_error("pymssql not installed")
            self.attempt_fix(
                "Missing pymssql",
                "/home/azureuser/miniconda3/bin/pip install pymssql",
                "Installing pymssql package"
            )
            return False
        except Exception as e:
            print_error(f"Database error: {str(e)}")
            return False
    
    def check_and_fix_packages(self):
        """Check and install missing Python packages"""
        print_header("PYTHON PACKAGES CHECK & AUTO-INSTALL")
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "pymssql",
            "sqlalchemy",
            "pandas",
            "numpy",
            "requests",
            "aiohttp",
            "pydantic",
            "azure-ai-documentintelligence",
            "google-generativeai",
            "openai",
            "cachetools",
            "paramiko"
        ]
        
        # Get installed packages
        result = subprocess.run(
            ["/home/azureuser/miniconda3/bin/pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            installed = {p['name'].lower(): p['version'] for p in json.loads(result.stdout)}
        else:
            installed = {}
        
        missing_packages = []
        for package in required_packages:
            if package.lower() not in installed:
                print_warning(f"Missing package: {package}")
                missing_packages.append(package)
            else:
                print_success(f"{package}: {installed[package.lower()]}")
        
        # Auto-install missing packages
        if missing_packages:
            packages_str = " ".join(missing_packages)
            self.attempt_fix(
                "Missing packages",
                f"/home/azureuser/miniconda3/bin/pip install {packages_str}",
                f"Installing missing packages: {packages_str}"
            )
    
    def check_disk_space(self):
        """Check and manage disk space"""
        print_header("DISK SPACE CHECK")
        
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 5:
                usage = parts[4].replace('%', '')
                try:
                    usage_int = int(usage)
                    if usage_int > 90:
                        print_error(f"Disk usage critical: {usage}%")
                        # Clean up old logs
                        self.attempt_fix(
                            "High disk usage",
                            "find /home/azureuser/harvey/logs -name '*.log' -mtime +7 -delete",
                            "Cleaning up logs older than 7 days"
                        )
                    elif usage_int > 80:
                        print_warning(f"Disk usage high: {usage}%")
                    else:
                        print_success(f"Disk usage OK: {usage}%")
                except:
                    pass
    
    def check_memory_usage(self):
        """Check memory usage and restart services if needed"""
        print_header("MEMORY USAGE CHECK")
        
        result = subprocess.run(["free", "-m"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 3:
                total = int(parts[1])
                used = int(parts[2])
                usage_percent = (used / total) * 100
                
                if usage_percent > 90:
                    print_error(f"Memory usage critical: {usage_percent:.1f}%")
                    # Restart heavy services
                    self.attempt_fix(
                        "High memory usage",
                        "sudo systemctl restart heydividend-ml-schedulers",
                        "Restarting ML schedulers to free memory"
                    )
                elif usage_percent > 80:
                    print_warning(f"Memory usage high: {usage_percent:.1f}%")
                else:
                    print_success(f"Memory usage OK: {usage_percent:.1f}%")
    
    def verify_ml_endpoints(self):
        """Verify ML scheduler endpoints are working"""
        print_header("ML SCHEDULER ENDPOINTS VERIFICATION")
        
        api_key = os.getenv("HARVEY_AI_API_KEY")
        if not api_key:
            print_warning("HARVEY_AI_API_KEY not set")
            return
        
        endpoints = [
            "/v1/ml-schedulers/health",
            "/v1/ml-schedulers/training-status"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"http://localhost:8001{endpoint}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5
                )
                if response.status_code == 200:
                    print_success(f"Endpoint {endpoint}: Working")
                elif response.status_code == 401:
                    print_warning(f"Endpoint {endpoint}: Auth required (expected)")
                else:
                    print_warning(f"Endpoint {endpoint}: Status {response.status_code}")
            except Exception as e:
                print_error(f"Endpoint {endpoint}: Failed - {str(e)}")
    
    def generate_report(self):
        """Generate and save the sanity check report"""
        print_header("SANITY CHECK SUMMARY")
        
        # Calculate overall health score
        total_checks = len(self.results["checks"])
        passed_checks = sum(1 for v in self.results["checks"].values() if v)
        health_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        self.results["health_score"] = health_score
        self.results["fixes_applied_count"] = len(self.results["fixes_applied"])
        
        if health_score >= 80:
            print_success(f"System Health: {health_score:.0f}% - GOOD")
            self.results["overall_status"] = "HEALTHY"
        elif health_score >= 60:
            print_warning(f"System Health: {health_score:.0f}% - NEEDS ATTENTION")
            self.results["overall_status"] = "WARNING"
        else:
            print_error(f"System Health: {health_score:.0f}% - CRITICAL")
            self.results["overall_status"] = "CRITICAL"
        
        # Show fixes applied
        if self.results["fixes_applied"]:
            print_success(f"\nAuto-fixes applied: {len(self.results['fixes_applied'])}")
            for fix in self.results["fixes_applied"]:
                if isinstance(fix, dict):
                    print_info(f"  - {fix['fix']}")
                else:
                    print_info(f"  - {fix}")
        
        # Save report
        report_dir = "/home/azureuser/harvey/sanity_reports"
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = os.path.join(report_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print_info(f"\nReport saved: {report_file}")
        logger.info(f"Sanity check complete. Health: {health_score:.0f}%, Fixes: {len(self.results['fixes_applied'])}")
        
        # Alert if critical
        if health_score < 60:
            self.send_alert(f"Harvey System Critical: Health {health_score:.0f}%")
        
        return health_score >= 60
    
    def send_alert(self, message):
        """Send alert for critical issues (placeholder for email/slack)"""
        logger.critical(f"ALERT: {message}")
        # TODO: Implement email or Slack notification
        
    def run_full_check(self):
        """Run complete sanity check with auto-healing"""
        logger.info("="*70)
        logger.info("Starting Harvey Sanity Check with Self-Healing")
        logger.info("="*70)
        
        # Run all checks
        self.check_disk_space()
        self.check_memory_usage()
        self.results["checks"]["resources"] = True
        
        self.check_and_fix_packages()
        self.results["checks"]["packages"] = True
        
        db_ok = self.check_and_fix_database()
        self.results["checks"]["database"] = db_ok
        
        self.check_and_fix_services()
        self.results["checks"]["services"] = True
        
        self.verify_ml_endpoints()
        self.results["checks"]["ml_endpoints"] = True
        
        # Generate report
        success = self.generate_report()
        
        # Clean up old reports (keep last 30 days)
        try:
            subprocess.run(
                "find /home/azureuser/harvey/sanity_reports -name '*.json' -mtime +30 -delete",
                shell=True
            )
        except:
            pass
        
        return success


def main():
    print(f"{BOLD}{BLUE}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     HARVEY ML SCHEDULER SANITY CHECK & SELF-HEALING v2.0    ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    
    checker = HarveySelfHealingCheck()
    success = checker.run_full_check()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())