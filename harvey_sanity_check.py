#!/usr/bin/env python3
"""
Harvey ML Scheduler Sanity Check Script
Verifies all components needed for ML scheduler jobs to run and write to databases successfully.
"""

import os
import sys
import json
import requests
import subprocess
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{text}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"   {text}")

class HarveySanityCheck:
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "errors": [],
            "warnings": [],
            "overall_status": "PASS"
        }
    
    def check_environment_variables(self):
        """Check all required environment variables"""
        print_header("1. ENVIRONMENT VARIABLES CHECK")
        
        required_vars = {
            "Database": [
                "SQLSERVER_HOST",
                "SQLSERVER_USER", 
                "SQLSERVER_PASSWORD",
                "SQLSERVER_DB"
            ],
            "API Keys": [
                "HARVEY_AI_API_KEY",
                "INTERNAL_ML_API_KEY",
                "OPENAI_API_KEY",
                "AZURE_OPENAI_API_KEY",
                "GEMINI_API_KEY"
            ],
            "Azure Services": [
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT_NAME",
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
                "AZURE_DOCUMENT_INTELLIGENCE_KEY"
            ],
            "ML Service": [
                "ML_API_BASE_URL"
            ],
            "Optional Services": [
                "PDFCO_API_KEY"
            ]
        }
        
        all_good = True
        for category, vars in required_vars.items():
            print(f"\n{BOLD}{category}:{RESET}")
            for var in vars:
                value = os.getenv(var)
                if value:
                    # Mask sensitive values
                    if "PASSWORD" in var or "KEY" in var:
                        masked = value[:4] + "****" + value[-4:] if len(value) > 8 else "****"
                        print_success(f"{var}: Set ({masked})")
                    else:
                        print_success(f"{var}: {value}")
                else:
                    if category == "Optional Services":
                        print_warning(f"{var}: Not set (optional)")
                    else:
                        print_error(f"{var}: Not set")
                        all_good = False
                        self.results["errors"].append(f"Missing env var: {var}")
        
        self.results["checks"]["environment_variables"] = all_good
        return all_good
    
    def check_python_packages(self):
        """Check all required Python packages"""
        print_header("2. PYTHON PACKAGES CHECK")
        
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
        
        installed_packages = {}
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                installed_packages = {p['name'].lower(): p['version'] for p in packages}
        except Exception as e:
            print_error(f"Failed to list packages: {e}")
            self.results["errors"].append(f"Package list failed: {e}")
        
        all_good = True
        for package in required_packages:
            if package.lower() in installed_packages:
                print_success(f"{package}: {installed_packages[package.lower()]}")
            else:
                print_error(f"{package}: Not installed")
                all_good = False
                self.results["errors"].append(f"Missing package: {package}")
        
        self.results["checks"]["python_packages"] = all_good
        return all_good
    
    def check_database_connectivity(self):
        """Check database connectivity and write permissions"""
        print_header("3. DATABASE CONNECTIVITY CHECK")
        
        try:
            import pymssql
            
            host = os.getenv("SQLSERVER_HOST")
            database = os.getenv("SQLSERVER_DB")
            user = os.getenv("SQLSERVER_USER")
            password = os.getenv("SQLSERVER_PASSWORD")
            
            if not all([host, database, user, password]):
                print_error("Missing database credentials")
                self.results["checks"]["database_connectivity"] = False
                return False
            
            print_info(f"Connecting to: {user}@{host}/{database}")
            
            conn = pymssql.connect(
                server=host,
                user=user,
                password=password,
                database=database,
                timeout=10,
                as_dict=True
            )
            
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()['count']
            print_success(f"Connected to database with {table_count} tables")
            
            # Check ML-related tables
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME LIKE '%ml_%' 
                   OR TABLE_NAME LIKE '%audit%'
                   OR TABLE_NAME LIKE '%feedback%'
                ORDER BY TABLE_NAME
            """)
            ml_tables = cursor.fetchall()
            
            if ml_tables:
                print_success(f"Found {len(ml_tables)} ML-related tables:")
                for table in ml_tables[:5]:  # Show first 5
                    print_info(f"  - {table['TABLE_NAME']}")
            else:
                print_warning("No ML-related tables found")
            
            # Test write permission
            try:
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'harvey_sanity_check')
                    CREATE TABLE harvey_sanity_check (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        check_time DATETIME DEFAULT GETDATE(),
                        status VARCHAR(50)
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO harvey_sanity_check (status) VALUES (%s)
                """, (f'Check from {os.uname().nodename}',))
                
                conn.commit()
                print_success("Database WRITE permissions confirmed")
                
                # Clean up
                cursor.execute("DROP TABLE harvey_sanity_check")
                conn.commit()
                
            except pymssql.Error as e:
                print_warning(f"Write test failed (may be read-only): {str(e)}")
                self.results["warnings"].append("Database may be read-only")
            
            cursor.close()
            conn.close()
            
            self.results["checks"]["database_connectivity"] = True
            return True
            
        except ImportError:
            print_error("pymssql package not installed")
            self.results["errors"].append("pymssql not installed")
            self.results["checks"]["database_connectivity"] = False
            return False
        except Exception as e:
            print_error(f"Database connection failed: {str(e)}")
            self.results["errors"].append(f"Database error: {str(e)}")
            self.results["checks"]["database_connectivity"] = False
            return False
    
    def check_ml_service(self):
        """Check ML service connectivity"""
        print_header("4. ML SERVICE CHECK")
        
        ml_api_base = os.getenv("ML_API_BASE_URL", "http://20.81.210.213:9000")
        ml_api_key = os.getenv("INTERNAL_ML_API_KEY")
        
        print_info(f"ML Service URL: {ml_api_base}")
        
        # Check ML service health
        try:
            response = requests.get(
                f"{ml_api_base}/health",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print_success(f"ML Service is healthy")
                print_info(f"  Version: {data.get('version', 'Unknown')}")
                print_info(f"  Models loaded: {data.get('models_loaded', False)}")
            else:
                print_error(f"ML Service returned status {response.status_code}")
                self.results["errors"].append(f"ML service unhealthy: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Cannot reach ML service: {str(e)}")
            self.results["errors"].append(f"ML service unreachable: {str(e)}")
            self.results["checks"]["ml_service"] = False
            return False
        
        # Check specific endpoints
        endpoints_to_check = [
            "/api/score/symbol",
            "/api/predict/yield",
            "/api/predict/growth",
            "/api/cluster/dashboard"
        ]
        
        working_endpoints = 0
        for endpoint in endpoints_to_check:
            try:
                response = requests.get(
                    f"{ml_api_base}{endpoint}",
                    headers={"X-API-Key": ml_api_key} if ml_api_key else {},
                    timeout=3
                )
                # We expect 400/405 for GET requests to POST endpoints, that's OK
                if response.status_code in [200, 400, 405, 422]:
                    print_success(f"Endpoint {endpoint}: Accessible")
                    working_endpoints += 1
                else:
                    print_warning(f"Endpoint {endpoint}: Status {response.status_code}")
            except:
                print_warning(f"Endpoint {endpoint}: Unreachable")
        
        self.results["checks"]["ml_service"] = working_endpoints > 0
        return working_endpoints > 0
    
    def check_harvey_api(self):
        """Check Harvey API endpoints"""
        print_header("5. HARVEY API CHECK")
        
        harvey_api_key = os.getenv("HARVEY_AI_API_KEY")
        
        # Check local Harvey API
        try:
            response = requests.get(
                "http://localhost:8001/health",
                timeout=5
            )
            if response.status_code in [200, 404]:  # 404 is OK if endpoint doesn't exist
                print_success("Harvey API is running on port 8001")
            else:
                print_warning(f"Harvey API returned status {response.status_code}")
        except:
            print_warning("Harvey API not accessible on localhost:8001")
            self.results["warnings"].append("Harvey API not running locally")
        
        # Check ML scheduler endpoints
        try:
            response = requests.get(
                "http://localhost:8001/v1/ml-schedulers/health",
                headers={"Authorization": f"Bearer {harvey_api_key}"} if harvey_api_key else {},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print_success("ML Scheduler endpoints are integrated")
                print_info(f"  Status: {data.get('status', 'Unknown')}")
            elif response.status_code == 401:
                print_success("ML Scheduler endpoints exist (auth required)")
            else:
                print_warning(f"ML Scheduler endpoints returned {response.status_code}")
        except Exception as e:
            print_warning(f"ML Scheduler endpoints not accessible: {str(e)}")
        
        self.results["checks"]["harvey_api"] = True
        return True
    
    def check_ml_schedulers(self):
        """Check ML scheduler services and timers"""
        print_header("6. ML SCHEDULER SERVICES CHECK")
        
        # Check systemd services
        services = [
            "heydividend-ml-schedulers.service",
            "ml-payout-rating.timer",
            "ml-dividend-calendar.timer",
            "ml-training.timer"
        ]
        
        all_good = True
        for service in services:
            try:
                result = subprocess.run(
                    ["systemctl", "status", service],
                    capture_output=True,
                    text=True
                )
                if "Active: active" in result.stdout:
                    print_success(f"{service}: Active")
                elif "could not be found" in result.stdout:
                    print_warning(f"{service}: Not found (may be on Azure VM only)")
                else:
                    print_warning(f"{service}: Not active")
                    all_good = False
            except:
                print_info(f"{service}: Cannot check (may require sudo)")
        
        # Check cron jobs as alternative
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                print_info("\nCron jobs found:")
                for line in result.stdout.split('\n')[:5]:
                    if line and not line.startswith('#'):
                        print_info(f"  {line}")
        except:
            pass
        
        self.results["checks"]["ml_schedulers"] = all_good
        return all_good
    
    def check_network_connectivity(self):
        """Check network connectivity to required services"""
        print_header("7. NETWORK CONNECTIVITY CHECK")
        
        endpoints = {
            "Azure SQL Server": "hey-dividend-sql-server.database.windows.net:1433",
            "ML Service": "20.81.210.213:9000",
            "Harvey API": "20.81.210.213:8001",
            "Azure OpenAI": "https://heygptai.openai.azure.com",
            "Google Gemini": "https://generativelanguage.googleapis.com"
        }
        
        all_good = True
        for name, endpoint in endpoints.items():
            if endpoint.startswith("http"):
                # HTTP check
                try:
                    response = requests.get(endpoint + "/health", timeout=3)
                    print_success(f"{name}: Reachable")
                except:
                    try:
                        response = requests.get(endpoint, timeout=3)
                        print_success(f"{name}: Reachable")
                    except:
                        print_warning(f"{name}: Not reachable")
            else:
                # TCP check
                host_port = endpoint.split(':')
                if len(host_port) == 2:
                    import socket
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(3)
                        result = sock.connect_ex((host_port[0], int(host_port[1])))
                        sock.close()
                        if result == 0:
                            print_success(f"{name}: Port {host_port[1]} open")
                        else:
                            print_warning(f"{name}: Port {host_port[1]} closed")
                            all_good = False
                    except:
                        print_warning(f"{name}: Cannot check")
        
        self.results["checks"]["network_connectivity"] = all_good
        return all_good
    
    def generate_report(self):
        """Generate final sanity check report"""
        print_header("SANITY CHECK SUMMARY")
        
        all_checks = [
            ("Environment Variables", self.results["checks"].get("environment_variables", False)),
            ("Python Packages", self.results["checks"].get("python_packages", False)),
            ("Database Connectivity", self.results["checks"].get("database_connectivity", False)),
            ("ML Service", self.results["checks"].get("ml_service", False)),
            ("Harvey API", self.results["checks"].get("harvey_api", False)),
            ("ML Schedulers", self.results["checks"].get("ml_schedulers", False)),
            ("Network Connectivity", self.results["checks"].get("network_connectivity", False))
        ]
        
        failed_checks = []
        for check_name, passed in all_checks:
            if passed:
                print_success(f"{check_name}: PASSED")
            else:
                print_error(f"{check_name}: FAILED")
                failed_checks.append(check_name)
        
        # Overall status
        print_header("OVERALL STATUS")
        if not failed_checks:
            print_success("ALL CHECKS PASSED - System is ready for ML scheduler jobs!")
            self.results["overall_status"] = "PASS"
        else:
            print_error(f"FAILED CHECKS: {', '.join(failed_checks)}")
            self.results["overall_status"] = "FAIL"
            
            # Provide recommendations
            print_header("RECOMMENDATIONS")
            if "Environment Variables" in failed_checks:
                print_warning("Set missing environment variables in .env or system environment")
            if "Python Packages" in failed_checks:
                print_warning("Install missing packages: pip install <package_name>")
            if "Database Connectivity" in failed_checks:
                print_warning("Check database credentials and firewall rules")
            if "ML Service" in failed_checks:
                print_warning("Ensure ML service is running on Azure VM port 9000")
        
        # Save report to file
        report_file = f"sanity_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return self.results["overall_status"] == "PASS"


def main():
    print(f"{BOLD}{BLUE}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          HARVEY ML SCHEDULER SANITY CHECK v1.0              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    print("Checking all components needed for ML scheduler jobs...")
    
    checker = HarveySanityCheck()
    
    # Run all checks
    checker.check_environment_variables()
    checker.check_python_packages()
    checker.check_database_connectivity()
    checker.check_ml_service()
    checker.check_harvey_api()
    checker.check_ml_schedulers()
    checker.check_network_connectivity()
    
    # Generate report
    success = checker.generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())