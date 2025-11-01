#!/usr/bin/env python3
"""
Harvey Intelligence Engine - Daily Model Training Runbook (Azure Automation)
This Python runbook runs on the Azure VM via Hybrid Runbook Worker

NO API ENDPOINTS NEEDED - Runs training scripts directly on the VM
"""

import os
import sys
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path

# Configuration
MODEL_DIR = Path("/home/azureuser/ml-prediction-api/models")
BACKUP_DIR = Path("/opt/harvey-intelligence/model-backups")
CONDA_ENV = "/home/azureuser/miniconda3/envs/llm/bin/activate"
SCRIPTS_DIR = Path("/home/azureuser/ml-prediction-api/scripts")
LOG_DIR = Path("/var/log/harvey-intelligence")

# Setup logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"azure-training-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_command(cmd, shell=False):
    """Execute shell command and return output"""
    try:
        if shell:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                executable='/bin/bash'
            )
        else:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {cmd}")
        logger.error(f"Error: {e.stderr}")
        raise


def backup_models():
    """Backup current production models"""
    logger.info("📦 Backing up current models...")
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)
    
    if MODEL_DIR.exists():
        # Copy all model files
        for ext in ["*.pkl", "*.joblib", "*.h5", "*.pt"]:
            run_command(f"cp {MODEL_DIR}/{ext} {backup_path}/ 2>/dev/null || true", shell=True)
        
        logger.info(f"✅ Models backed up to: {backup_path}")
        
        # Save backup path for potential rollback
        (BACKUP_DIR / "latest_backup.txt").write_text(str(backup_path))
        return backup_path
    else:
        logger.warning(f"⚠️ Model directory not found: {MODEL_DIR}")
        return None


def rollback_models(backup_path):
    """Restore models from backup"""
    logger.info("⏪ Rolling back to previous model version...")
    
    if backup_path and backup_path.exists():
        run_command(f"cp {backup_path}/*.pkl {MODEL_DIR}/ 2>/dev/null || true", shell=True)
        run_command(f"cp {backup_path}/*.joblib {MODEL_DIR}/ 2>/dev/null || true", shell=True)
        logger.info(f"✅ Models restored from: {backup_path}")
        
        # Restart Intelligence Engine
        restart_intelligence_engine()
    else:
        logger.error("❌ No backup available for rollback")
        raise Exception("Rollback failed - no backup found")


def cleanup_old_backups(keep_count=7):
    """Keep only the most recent N backups"""
    logger.info(f"🧹 Cleaning up old backups (keeping last {keep_count})...")
    
    if BACKUP_DIR.exists():
        backups = sorted(BACKUP_DIR.glob("backup_*"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_backup in backups[keep_count:]:
            run_command(f"rm -rf {old_backup}", shell=True)
            logger.info(f"Deleted old backup: {old_backup.name}")
        
        logger.info("✅ Old backups cleaned up")


def train_models():
    """Execute model training scripts"""
    logger.info("🚀 Starting model training...")
    
    # Activate conda environment and run training
    activate_cmd = f"source {CONDA_ENV}"
    
    # Find training script
    training_script = None
    for script_name in ["train_all_models.py", "train.py", "main_training.py"]:
        script_path = SCRIPTS_DIR / script_name
        if script_path.exists():
            training_script = script_path
            break
    
    if not training_script:
        raise FileNotFoundError(f"No training script found in {SCRIPTS_DIR}")
    
    logger.info(f"Found training script: {training_script}")
    
    # Run training
    cmd = f"{activate_cmd} && cd {SCRIPTS_DIR} && python {training_script.name}"
    output = run_command(cmd, shell=True)
    
    logger.info("Training output:")
    logger.info(output)
    logger.info("✅ Training completed successfully")


def validate_models():
    """Validate trained models meet quality thresholds"""
    logger.info("🔍 Validating new models...")
    
    activate_cmd = f"source {CONDA_ENV}"
    
    # Find validation script
    validation_script = None
    for script_name in ["validate_models.py", "validate.py"]:
        script_path = SCRIPTS_DIR / script_name
        if script_path.exists():
            validation_script = script_path
            break
    
    if not validation_script:
        logger.warning("⚠️ No validation script found, skipping validation")
        return True
    
    logger.info(f"Found validation script: {validation_script}")
    
    # Run validation
    try:
        cmd = f"{activate_cmd} && cd {SCRIPTS_DIR} && python {validation_script.name}"
        output = run_command(cmd, shell=True)
        logger.info("Validation output:")
        logger.info(output)
        logger.info("✅ Model validation passed")
        return True
    except Exception as e:
        logger.error(f"❌ Model validation failed: {e}")
        return False


def restart_intelligence_engine():
    """Restart Intelligence Engine service to load new models"""
    logger.info("🔄 Restarting Intelligence Engine...")
    
    try:
        # Try new service name first
        run_command(["sudo", "systemctl", "restart", "harvey-intelligence.service"])
        logger.info("✅ harvey-intelligence.service restarted")
    except:
        try:
            # Fall back to old service name
            run_command(["sudo", "systemctl", "restart", "ml-api.service"])
            logger.info("✅ ml-api.service restarted")
        except Exception as e:
            logger.error(f"❌ Failed to restart Intelligence Engine: {e}")
            raise
    
    # Wait for service to be ready
    import time
    time.sleep(5)
    
    # Test health endpoint
    try:
        import urllib.request
        response = urllib.request.urlopen("http://127.0.0.1:9000/api/internal/ml/health", timeout=10)
        if response.status == 200:
            logger.info("✅ Intelligence Engine is healthy")
        else:
            raise Exception(f"Health check returned status {response.status}")
    except Exception as e:
        logger.error(f"❌ Intelligence Engine health check failed: {e}")
        raise


def send_notification(message, success=True):
    """Send notification via Slack/email (optional)"""
    # Get Slack webhook from environment or Azure Automation variable
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
    
    if not slack_webhook:
        logger.info("No Slack webhook configured, skipping notification")
        return
    
    try:
        import urllib.request
        import json
        
        emoji = "✅" if success else "❌"
        payload = {
            "text": f"{emoji} Harvey Intelligence Engine: {message}",
            "username": "Azure Automation"
        }
        
        req = urllib.request.Request(
            slack_webhook,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
        logger.info(f"Sent notification: {message}")
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")


def main():
    """Main training workflow"""
    logger.info("═══════════════════════════════════════════════════")
    logger.info("🤖 Harvey Intelligence Engine - Daily Training (Azure Automation)")
    logger.info("═══════════════════════════════════════════════════")
    
    backup_path = None
    
    try:
        send_notification("Daily model training started", success=True)
        
        # Step 1: Backup current models
        backup_path = backup_models()
        
        # Step 2: Train new models
        train_models()
        
        # Step 3: Validate new models
        if not validate_models():
            raise Exception("Model validation failed")
        
        # Step 4: Restart Intelligence Engine
        restart_intelligence_engine()
        
        # Step 5: Cleanup old backups
        cleanup_old_backups(keep_count=7)
        
        # Success!
        logger.info("═══════════════════════════════════════════════════")
        logger.info("✅ Daily training completed successfully!")
        logger.info("═══════════════════════════════════════════════════")
        logger.info(f"📝 Full log: {log_file}")
        
        send_notification("Daily training completed successfully!", success=True)
        
        return {
            "status": "success",
            "message": "Training completed successfully",
            "log_file": str(log_file),
            "backup_path": str(backup_path) if backup_path else None
        }
        
    except Exception as e:
        error_msg = f"Training failed: {str(e)}"
        logger.error("═══════════════════════════════════════════════════")
        logger.error(f"❌ {error_msg}")
        logger.error("═══════════════════════════════════════════════════")
        
        # Rollback to backup
        if backup_path:
            try:
                rollback_models(backup_path)
                send_notification(f"{error_msg} - Rolled back to previous models", success=False)
            except Exception as rollback_error:
                logger.error(f"Rollback also failed: {rollback_error}")
                send_notification(f"{error_msg} - ROLLBACK FAILED", success=False)
        else:
            send_notification(error_msg, success=False)
        
        raise


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
