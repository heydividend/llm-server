#!/usr/bin/env python3
"""
Harvey ML Scheduler Sanity Check v4.0 - Fixed Timer Issues
Checks system health and sends email alerts when issues are detected.
"""

import os
import sys
import json
import subprocess
import requests
import logging
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sanity_check.log')
    ]
)

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{'═'*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'═'*70}{Colors.ENDC}")

def print_section(text):
    print(f"\n{'='*70}")
    print(text)
    print(f"{'='*70}")
    logging.info(text)

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")
    logging.info(f"✅ {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")
    logging.warning(f"⚠️  {text}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")
    logging.error(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")
    logging.info(text)

class EmailAlertService:
    """Email alert service using SendGrid"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("ALERT_EMAIL_FROM", "harvey@heydividend.com")
        self.to_emails = os.getenv("ALERT_EMAIL_TO", "dev@heydividend.com").split(",")
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            print_warning("SendGrid email alerts disabled (no API key)")
            logging.warning("SendGrid email alerts disabled (no API key)")
        else:
            print_success("SendGrid email alerts enabled")
            logging.info("SendGrid email alerts enabled")
    
    def send_alert(self, subject: str, body: str, alert_level: str = "WARNING"):
        """Send email alert via SendGrid"""
        if not self.enabled:
            print_warning("Email alert not sent (disabled): " + subject)
            logging.warning(f"Email alert not sent (disabled): {subject}")
            return False
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            # Create HTML content
            color = "#ff9800" if alert_level == "WARNING" else "#f44336"
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
                    .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    h2 {{ color: #2c3e50; border-bottom: 2px solid {color}; padding-bottom: 10px; }}
                    .alert-box {{ background: #fff3cd; border-left: 4px solid {color}; padding: 15px; margin: 20px 0; }}
                    .details {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                    pre {{ background: #2c3e50; color: #fff; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                    ul {{ line-height: 1.8; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Harvey ML System Alert</h2>
                    <div class="alert-box">
                        <strong>Severity:</strong> {alert_level}<br>
                        <strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                        <strong>VM:</strong> {socket.gethostname()}
                    </div>
                    
                    <h3>Subject: {subject}</h3>
                    
                    <div class="details">
                        <h4>Details:</h4>
                        <pre>{body}</pre>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated alert from the Harvey ML Scheduler Sanity Check system running on Azure VM 20.81.210.213</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = Mail(
                from_email=self.from_email,
                to_emails=self.to_emails,
                subject=f'[{alert_level}] Harvey Sanity Check: {subject}',
                html_content=html_content
            )
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                print_success(f"Email alert sent successfully to {', '.join(self.to_emails)}")
                logging.info(f"Email alert sent successfully to {', '.join(self.to_emails)}")
                return True
            else:
                print_error(f"SendGrid returned status {response.status_code}")
                logging.error(f"SendGrid returned status {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Failed to send email alert: {str(e)}")
            logging.error(f"Failed to send email alert: {str(e)}")
            return False

class HarveySelfHealingCheck:
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": 100,
            "status": "OK",
            "checks_performed": 0,
            "checks_passed": 0,
            "checks_failed": 0,
            "critical_issues": [],
            "warnings": [],
            "fixes_applied": [],
            "service_status": {},
            "cron_status": {}  # Separate tracking for cron jobs
        }
        
        self.critical_issues = []
        self.warnings = []
        self.fixes_applied = []
        self.service_status = {}
        self.cron_status = {}  # Track cron jobs separately
        
        # Email alert service
        self.email_service = EmailAlertService()
        
        # Load environment variables from .env if exists
        self.load_env()
    
    def load_env(self):
        """Load environment variables from .env file if it exists"""
        env_path = Path('/home/azureuser/harvey/.env')
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key not in os.environ:
                            os.environ[key] = value
    
    def attempt_fix(self, issue: str, fix_command: str, fix_description: str) -> bool:
        """Attempt to fix an issue and track the result"""
        try:
            logging.info(f"Auto-fix attempt: {fix_description}")
            result = subprocess.run(fix_command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print_success(f"✅ Fixed: {fix_description}")
                self.fixes_applied.append(fix_description)
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print_warning(f"Fix failed: {error_msg}")
                self.critical_issues.append(f"Failed to fix: {fix_description}")
                return False
        except subprocess.TimeoutExpired:
            print_warning(f"Fix timeout: {fix_description}")
            self.critical_issues.append(f"Fix timeout: {fix_description}")
            return False
        except Exception as e:
            print_warning(f"Fix error: {str(e)}")
            self.critical_issues.append(f"Fix error for {fix_description}: {str(e)}")
            return False
    
    def check_disk_space(self):
        """Check disk space usage"""
        print_section("DISK SPACE CHECK")
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                usage_line = lines[1].split()
                usage_percent = int(usage_line[4].strip('%'))
                
                if usage_percent < 80:
                    print_success(f"Disk usage OK: {usage_percent}%")
                elif usage_percent < 90:
                    print_warning(f"Disk usage high: {usage_percent}%")
                    self.warnings.append(f"Disk usage at {usage_percent}%")
                else:
                    print_error(f"Critical disk usage: {usage_percent}%")
                    self.critical_issues.append(f"Disk usage critical: {usage_percent}%")
                    
                    # Attempt to clean up
                    if self.attempt_fix(
                        "High disk usage",
                        "sudo apt-get clean && sudo journalctl --vacuum-time=3d",
                        "Cleaning apt cache and old logs"
                    ):
                        print_success("Freed up disk space")
        except Exception as e:
            print_error(f"Could not check disk space: {str(e)}")
            self.warnings.append(f"Could not check disk space: {str(e)}")
    
    def check_memory(self):
        """Check memory usage"""
        print_section("MEMORY USAGE CHECK")
        try:
            result = subprocess.run(['free', '-m'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                mem_line = lines[1].split()
                total = int(mem_line[1])
                used = int(mem_line[2])
                usage_percent = (used / total) * 100
                
                if usage_percent < 80:
                    print_success(f"Memory usage OK: {usage_percent:.1f}%")
                elif usage_percent < 90:
                    print_warning(f"Memory usage high: {usage_percent:.1f}%")
                    self.warnings.append(f"Memory usage at {usage_percent:.1f}%")
                else:
                    print_error(f"Critical memory usage: {usage_percent:.1f}%")
                    self.critical_issues.append(f"Memory usage critical: {usage_percent:.1f}%")
        except Exception as e:
            print_error(f"Could not check memory: {str(e)}")
            self.warnings.append(f"Could not check memory: {str(e)}")
    
    def check_services(self):
        """Check if critical services are running"""
        print_section("SERVICE HEALTH CHECK & AUTO-HEALING")
        service_status = {}
        
        # Check Harvey API
        try:
            response = requests.get("http://localhost:8001/health", timeout=3)
            if response.status_code == 200:
                print_success("Harvey API is running")
                service_status["harvey_api"] = "running"
            else:
                raise Exception(f"Status {response.status_code}")
        except:
            print_error("Harvey API is not responding")
            service_status["harvey_api"] = "down"
            
            # Try to restart Harvey API
            if not self.attempt_fix(
                "Harvey API down",
                "sudo systemctl restart harvey || cd /home/azureuser/harvey && nohup uvicorn main:app --host 0.0.0.0 --port 8001 > harvey.log 2>&1 &",
                "Restarting Harvey API on port 8001"
            ):
                self.critical_issues.append("Harvey API is down and could not be restarted")
        
        # Check ML Service
        try:
            response = requests.get("http://localhost:9000/health", timeout=3)
            if response.status_code == 200:
                print_success("ML Service is running")
                service_status["ml_service"] = "running"
            else:
                raise Exception(f"Status {response.status_code}")
        except:
            print_error("ML Service is not responding")
            service_status["ml_service"] = "down"
            
            # Try to restart ML service
            if not self.attempt_fix(
                "ML Service down",
                "sudo systemctl restart heydividend-ml-service || cd /home/azureuser/ml-service && nohup python main.py > ml.log 2>&1 &",
                "Restarting ML Service on port 9000"
            ):
                self.critical_issues.append("ML Service is down and could not be restarted")
        
        # Check ML scheduler cron jobs separately (not as critical services)
        print_section("ML SCHEDULER CRON JOBS CHECK")
        
        cron_jobs = {
            "ML Payout Rating (Daily 1AM)": "run_ml_payout_rating.py",
            "ML Dividend Calendar (Sunday 2AM)": "run_ml_dividend_calendar.py",
            "ML Training (Sunday 3AM)": "run_ml_training.py",
            "Sanity Check (Daily 2AM)": "harvey_sanity_check"
        }
        
        try:
            # Get current user's crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                crontab_content = result.stdout
                cron_configured = 0
                
                for job_name, script_pattern in cron_jobs.items():
                    if script_pattern in crontab_content:
                        print_success(f"{job_name} is configured")
                        self.cron_status[job_name] = "configured"
                        cron_configured += 1
                    else:
                        print_info(f"{job_name} not found in crontab")
                        self.cron_status[job_name] = "not_found"
                
                if cron_configured == len(cron_jobs):
                    print_success("All ML scheduler cron jobs are configured")
                elif cron_configured > 0:
                    print_info(f"{cron_configured}/{len(cron_jobs)} cron jobs configured")
                    # This is informational, not a critical issue
                else:
                    print_info("No ML scheduler cron jobs found (may be using different scheduling)")
            else:
                print_info("No crontab configured (cron jobs may be in /etc/cron.d/)")
                # Check system-wide cron
                if Path('/etc/cron.d/').exists():
                    for cron_file in Path('/etc/cron.d/').glob('*'):
                        try:
                            content = cron_file.read_text()
                            for job_name, script_pattern in cron_jobs.items():
                                if script_pattern in content:
                                    print_success(f"{job_name} found in {cron_file.name}")
                                    self.cron_status[job_name] = "system_cron"
                        except:
                            pass
        except Exception as e:
            print_info(f"Could not check cron jobs: {str(e)}")
            # Not a critical issue - just informational
        
        self.service_status = service_status
        self.results["service_status"] = service_status
        self.results["cron_status"] = self.cron_status
        
        # Only return failure if actual services are down, not cron jobs
        return all(v == "running" for v in service_status.values())
    
    def check_python_packages(self):
        """Check and auto-install required Python packages"""
        print_section("PYTHON PACKAGES CHECK & AUTO-INSTALL")
        
        required_packages = [
            "fastapi", "uvicorn", "pymssql", "sqlalchemy",
            "pandas", "numpy", "requests", "aiohttp",
            "pydantic", "azure-ai-documentintelligence",
            "google-generativeai", "openai", "cachetools",
            "paramiko", "sendgrid"
        ]
        
        for package in required_packages:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", f"import {package.replace('-', '_')}; print({package.replace('-', '_')}.__version__)"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print_success(f"{package}: {version}")
                else:
                    raise ImportError(f"{package} not found")
            except:
                print_warning(f"{package} not installed")
                if self.attempt_fix(
                    f"Missing {package}",
                    f"{sys.executable} -m pip install {package}",
                    f"Installing {package}"
                ):
                    print_success(f"Installed {package}")
    
    def check_database(self):
        """Check database connectivity and tables"""
        print_section("DATABASE CONNECTIVITY & HEALING")
        
        try:
            import pymssql
            
            # Get database credentials
            host = os.getenv("SQLSERVER_HOST")
            database = os.getenv("SQLSERVER_DB")
            username = os.getenv("SQLSERVER_USER")
            password = os.getenv("SQLSERVER_PASSWORD")
            
            if not all([host, database, username, password]):
                print_error("Database credentials not configured")
                self.critical_issues.append("Database credentials not configured")
                
                # Try to load from .env
                if self.attempt_fix(
                    "Missing DB credentials",
                    "source /home/azureuser/harvey/.env",
                    "Loading environment variables from .env file"
                ):
                    # Re-check after loading
                    host = os.getenv("SQLSERVER_HOST")
                    database = os.getenv("SQLSERVER_DB")
                    username = os.getenv("SQLSERVER_USER")
                    password = os.getenv("SQLSERVER_PASSWORD")
                
                if not all([host, database, username, password]):
                    return False
            
            # Connect to database
            conn = pymssql.connect(
                server=host,
                user=username,
                password=password,
                database=database,
                timeout=10
            )
            
            cursor = conn.cursor(as_dict=True)
            
            # Check table count
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()['count']
            print_success(f"Database connected: {table_count} tables found")
            
            # Check for critical tables
            critical_tables = ["tickers", "dividend_history", "ticker_info"]
            missing_tables = []
            
            for table in critical_tables:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{table}'
                """)
                if cursor.fetchone()['count'] == 0:
                    print_warning(f"Missing table: {table}")
                    missing_tables.append(table)
                    # Create table if missing
                    try:
                        if table == "user_feedback":
                            cursor.execute("""
                                CREATE TABLE user_feedback (
                                    id INT IDENTITY(1,1) PRIMARY KEY,
                                    user_id VARCHAR(255),
                                    message_id VARCHAR(255),
                                    feedback VARCHAR(50),
                                    created_at DATETIME DEFAULT GETDATE()
                                )
                            """)
                            conn.commit()
                            print_success(f"Created missing table: {table}")
                            self.results["fixes_applied"].append(f"Created table: {table}")
                    except:
                        pass
            
            if missing_tables:
                self.results["warnings"].append(f"Missing tables: {', '.join(missing_tables)}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print_error(f"Database error: {str(e)}")
            self.critical_issues.append(f"Database connection failed: {str(e)}")
            return False
    
    def check_ml_endpoints(self):
        """Check ML scheduler endpoints"""
        print_section("ML SCHEDULER ENDPOINTS VERIFICATION")
        
        api_key = os.getenv("HARVEY_AI_API_KEY")
        if not api_key:
            print_warning("HARVEY_AI_API_KEY not set")
            self.warnings.append("HARVEY_AI_API_KEY not set")
            return
        
        endpoints = [
            "/v1/ml-schedulers/health",
            "/v1/ml-schedulers/training-status"
        ]
        
        headers = {"Authorization": f"Bearer {api_key}"}
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"http://localhost:8001{endpoint}",
                    headers=headers,
                    timeout=5
                )
                if response.status_code == 200:
                    print_success(f"Endpoint {endpoint}: Working")
                else:
                    print_warning(f"Endpoint {endpoint}: Status {response.status_code}")
                    self.warnings.append(f"ML endpoint {endpoint} returned {response.status_code}")
            except Exception as e:
                print_error(f"Endpoint {endpoint}: Failed - {str(e)}")
                self.warnings.append(f"ML endpoint {endpoint} failed: {str(e)}")
    
    def calculate_health_score(self):
        """Calculate overall system health score"""
        score = 100
        
        # Critical issues reduce score significantly
        score -= len(self.critical_issues) * 10
        
        # Warnings reduce score slightly
        score -= len(self.warnings) * 2
        
        # Service status affects score
        for service, status in self.service_status.items():
            if status != "running":
                score -= 15
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        return score
    
    def run_checks(self):
        """Run all sanity checks"""
        print_header("HARVEY ML SCHEDULER SANITY CHECK v4.0 FIXED")
        print(f"\n{Colors.BLUE}Starting comprehensive system check...{Colors.ENDC}\n")
        
        checks = [
            self.check_disk_space,
            self.check_memory,
            self.check_python_packages,
            self.check_database,
            self.check_services,
            self.check_ml_endpoints
        ]
        
        for check in checks:
            try:
                self.results["checks_performed"] += 1
                result = check()
                if result is not False:
                    self.results["checks_passed"] += 1
                else:
                    self.results["checks_failed"] += 1
            except Exception as e:
                self.results["checks_failed"] += 1
                print_error(f"Check failed with error: {str(e)}")
                logging.error(f"Check failed: {str(e)}")
        
        # Update results
        self.results["critical_issues"] = self.critical_issues
        self.results["warnings"] = self.warnings
        self.results["fixes_applied"] = self.fixes_applied
        
        # Calculate health score
        health_score = self.calculate_health_score()
        self.results["health_score"] = health_score
        
        # Determine status
        if health_score >= 90:
            self.results["status"] = "OK"
            status_text = "EXCELLENT"
        elif health_score >= 80:
            self.results["status"] = "WARNING"
            status_text = "GOOD"
        elif health_score >= 70:
            self.results["status"] = "WARNING"
            status_text = "NEEDS ATTENTION"
        else:
            self.results["status"] = "CRITICAL"
            status_text = "CRITICAL"
        
        # Print summary
        print_section("SANITY CHECK SUMMARY")
        
        if health_score >= 80:
            print_success(f"System Health: {health_score}% - {status_text}")
        elif health_score >= 70:
            print_warning(f"System Health: {health_score}% - {status_text}")
        else:
            print_error(f"System Health: {health_score}% - {status_text}")
        
        if self.critical_issues:
            print_error(f"\nCritical Issues: {len(self.critical_issues)}")
            for issue in self.critical_issues:
                print(f"     - {issue}")
                logging.info(f"     - {issue}")
        
        if self.warnings:
            print_warning(f"\nWarnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"     - {warning}")
                logging.info(f"     - {warning}")
        
        if self.fixes_applied:
            print_success(f"\nAuto-Fixes Applied: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                print(f"     - {fix}")
                logging.info(f"     - {fix}")
        
        # Save report
        report_dir = Path("/home/azureuser/harvey/sanity_reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"   \nReport saved: {report_file}")
        logging.info(f"   \nReport saved: {report_file}")
        
        # Send email alert if health is below threshold
        if health_score < 80:
            alert_level = "CRITICAL" if health_score < 70 else "WARNING"
            
            # Format report for email
            report_text = f"""Harvey ML Scheduler Sanity Check Report
========================================
Health Score: {health_score}%
Status: {status_text}
Time: {self.results['timestamp']}

Checks Performed: {self.results['checks_performed']}
Passed: {self.results['checks_passed']}
Failed: {self.results['checks_failed']}

Auto-Fixes Applied: {len(self.fixes_applied)}
"""
            
            if self.critical_issues:
                report_text += f"\n\nCritical Issues: {len(self.critical_issues)}\n"
                for issue in self.critical_issues:
                    report_text += f"  - {issue}\n"
            
            if self.warnings:
                report_text += f"\nWarnings: {len(self.warnings)}\n"
                for warning in self.warnings:
                    report_text += f"  - {warning}\n"
            
            report_text += f"\nService Status:\n{json.dumps(self.service_status, indent=2)}"
            
            if self.cron_status:
                report_text += f"\n\nCron Job Status:\n{json.dumps(self.cron_status, indent=2)}"
            
            report_text += f"\n\nFull report: {report_file}"
            
            # Send email alert
            self.email_service.send_alert(
                subject=f"System Health: {health_score}% - {alert_level}",
                body=report_text,
                alert_level=alert_level
            )
        else:
            print_success("Email alert not needed (health >= 80%)")
        
        # Log completion
        logging.info(f"Sanity check complete. Health: {health_score}%, Fixes: {len(self.fixes_applied)}, Critical Issues: {len(self.critical_issues)}")
        
        return health_score >= 70  # Return True if health is acceptable

def main():
    try:
        checker = HarveySelfHealingCheck()
        success = checker.run_checks()
        
        # Exit with appropriate code
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Fatal error: {str(e)}")
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()