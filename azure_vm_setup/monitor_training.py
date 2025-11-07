#!/usr/bin/env python3
"""
Harvey ML Training Monitor
Monitors training status, model performance, and health metrics
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List
import subprocess
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

class TrainingMonitor:
    """Monitor ML training status and model health."""
    
    def __init__(self, base_dir: str = "/home/harvey/harvey-backend/ml_training"):
        """Initialize monitor."""
        self.base_dir = base_dir
        self.models_dir = os.path.join(base_dir, "models")
        self.metrics_file = os.path.join(base_dir, "training_metrics.json")
        self.status_file = "/var/log/harvey/training_status.json"
        
        self.model_names = [
            'dividend_scorer',
            'yield_predictor',
            'growth_predictor',
            'payout_predictor',
            'cut_risk_analyzer',
            'anomaly_detector',
            'stock_clusterer'
        ]
    
    def get_model_status(self) -> List[Dict[str, Any]]:
        """Get status of all models."""
        status_list = []
        
        for model in self.model_names:
            model_file = os.path.join(self.models_dir, f"{model}.pkl")
            status = {
                "model": model,
                "exists": os.path.exists(model_file)
            }
            
            if status["exists"]:
                # Get file stats
                stat = os.stat(model_file)
                status["size_mb"] = round(stat.st_size / (1024 * 1024), 2)
                status["modified"] = datetime.fromtimestamp(stat.st_mtime)
                status["age_days"] = (datetime.now() - status["modified"]).days
                
                # Determine health
                if status["age_days"] <= 7:
                    status["health"] = "🟢 Good"
                elif status["age_days"] <= 30:
                    status["health"] = "🟡 Aging"
                else:
                    status["health"] = "🔴 Stale"
            else:
                status["size_mb"] = 0
                status["modified"] = None
                status["age_days"] = None
                status["health"] = "⚫ Missing"
            
            status_list.append(status)
        
        return status_list
    
    def get_training_metrics(self) -> Dict[str, Any]:
        """Load latest training metrics."""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading metrics: {e}")
        return {}
    
    def get_service_status(self) -> Dict[str, str]:
        """Get status of ML services."""
        services = {
            "harvey-ml": "ML API Service",
            "harvey-ml-training": "Training Service"
        }
        
        status_dict = {}
        for service, name in services.items():
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True
                )
                status = result.stdout.strip()
                
                if status == "active":
                    status_dict[name] = f"{Fore.GREEN}● Active{Style.RESET_ALL}"
                elif status == "inactive":
                    status_dict[name] = f"{Fore.RED}○ Inactive{Style.RESET_ALL}"
                else:
                    status_dict[name] = f"{Fore.YELLOW}◐ {status}{Style.RESET_ALL}"
                    
            except Exception:
                status_dict[name] = f"{Fore.RED}✗ Unknown{Style.RESET_ALL}"
        
        return status_dict
    
    def get_api_health(self) -> Dict[str, Any]:
        """Check ML API health."""
        try:
            import requests
            response = requests.get(
                "http://localhost:9000/api/internal/ml/models/status",
                headers={"X-API-Key": os.getenv("INTERNAL_ML_API_KEY", "")},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": f"{Fore.GREEN}Healthy{Style.RESET_ALL}",
                    "models_loaded": data.get("models_loaded", False),
                    "model_version": data.get("model_version", "Unknown")
                }
            else:
                return {
                    "status": f"{Fore.RED}Error ({response.status_code}){Style.RESET_ALL}",
                    "models_loaded": False
                }
                
        except Exception as e:
            return {
                "status": f"{Fore.RED}Offline{Style.RESET_ALL}",
                "error": str(e)
            }
    
    def display_status(self):
        """Display comprehensive status."""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}Harvey ML Training Status Monitor{Style.RESET_ALL}")
        print("=" * 80)
        
        # Service Status
        print(f"\n{Fore.YELLOW}📊 Service Status:{Style.RESET_ALL}")
        services = self.get_service_status()
        for name, status in services.items():
            print(f"  {name}: {status}")
        
        # API Health
        print(f"\n{Fore.YELLOW}🌐 ML API Health:{Style.RESET_ALL}")
        api_health = self.get_api_health()
        for key, value in api_health.items():
            if key != "error":
                print(f"  {key}: {value}")
        
        # Model Status
        print(f"\n{Fore.YELLOW}🤖 Model Status:{Style.RESET_ALL}")
        models = self.get_model_status()
        
        table_data = []
        for model in models:
            table_data.append([
                model["model"],
                model["health"],
                f"{model['size_mb']} MB" if model["exists"] else "N/A",
                f"{model['age_days']} days" if model["age_days"] is not None else "N/A",
                model["modified"].strftime("%Y-%m-%d %H:%M") if model["modified"] else "Never"
            ])
        
        headers = ["Model", "Health", "Size", "Age", "Last Modified"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Training Metrics
        metrics = self.get_training_metrics()
        if metrics:
            print(f"\n{Fore.YELLOW}📈 Latest Training Results:{Style.RESET_ALL}")
            
            if "models" in metrics:
                successful = sum(1 for m in metrics["models"].values() 
                               if m.get("status") == "success")
                total = len(metrics["models"])
                
                print(f"  Success Rate: {successful}/{total} models")
                print(f"  Last Training: {metrics.get('end_time', 'Unknown')}")
                
                # Show failed models if any
                failed = [name for name, result in metrics["models"].items() 
                         if result.get("status") not in ["success", "skipped"]]
                if failed:
                    print(f"  {Fore.RED}Failed Models: {', '.join(failed)}{Style.RESET_ALL}")
        
        # System Resources
        print(f"\n{Fore.YELLOW}💻 System Resources:{Style.RESET_ALL}")
        try:
            # Disk usage
            result = subprocess.run(
                ["df", "-h", self.base_dir],
                capture_output=True,
                text=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    print(f"  Disk Usage: {parts[4]} ({parts[2]} used / {parts[1]} total)")
            
            # Memory usage
            result = subprocess.run(
                ["free", "-h"],
                capture_output=True,
                text=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 3:
                    print(f"  Memory: {parts[2]} used / {parts[1]} total")
                    
        except Exception as e:
            print(f"  Error getting system stats: {e}")
        
        print("\n" + "=" * 80)
    
    def watch_logs(self, service: str = "harvey-ml-training"):
        """Watch training logs in real-time."""
        print(f"\n{Fore.CYAN}Watching logs for {service}...{Style.RESET_ALL}")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            subprocess.run(["journalctl", "-u", service, "-f"])
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Stopped watching logs{Style.RESET_ALL}")
    
    def trigger_training(self, model: str = None, force: bool = False):
        """Manually trigger training."""
        if model:
            print(f"\n{Fore.CYAN}Triggering training for {model}...{Style.RESET_ALL}")
            cmd = ["python", os.path.join(self.base_dir, "train.py"), 
                   "--model", model]
        else:
            print(f"\n{Fore.CYAN}Triggering training for all models...{Style.RESET_ALL}")
            cmd = ["python", os.path.join(self.base_dir, "automated_training.py"),
                   "--mode", "once"]
            
        if force:
            cmd.append("--force")
        
        try:
            subprocess.run(cmd, cwd=self.base_dir)
            print(f"{Fore.GREEN}Training completed{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Training failed: {e}{Style.RESET_ALL}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Harvey ML Training Monitor')
    parser.add_argument('--watch', action='store_true',
                       help='Watch training logs in real-time')
    parser.add_argument('--train', metavar='MODEL',
                       help='Trigger training for specific model (or "all")')
    parser.add_argument('--force', action='store_true',
                       help='Force retraining even if models exist')
    parser.add_argument('--json', action='store_true',
                       help='Output status in JSON format')
    
    args = parser.parse_args()
    
    monitor = TrainingMonitor()
    
    if args.watch:
        monitor.watch_logs()
    elif args.train:
        model = None if args.train == "all" else args.train
        monitor.trigger_training(model, args.force)
    elif args.json:
        # Output status as JSON
        status = {
            "models": monitor.get_model_status(),
            "services": monitor.get_service_status(),
            "api": monitor.get_api_health(),
            "metrics": monitor.get_training_metrics()
        }
        print(json.dumps(status, indent=2, default=str))
    else:
        monitor.display_status()


if __name__ == "__main__":
    main()