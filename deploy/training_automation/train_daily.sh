#!/bin/bash
# Harvey Intelligence Engine - Daily Model Training Script
# This script runs nightly to retrain ML models with latest market data

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/harvey-intelligence"
LOG_FILE="$LOG_DIR/training-$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="/opt/harvey-intelligence/model-backups"
MODEL_DIR="/home/azureuser/ml-prediction-api/models"
CONDA_BASE="/home/azureuser/miniconda3"
CONDA_ENV_NAME="llm"
SCRIPTS_DIR="/home/azureuser/ml-prediction-api/scripts"

# Slack webhook (optional - set in environment)
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"

# Create directories if they don't exist
sudo mkdir -p "$LOG_DIR"
sudo mkdir -p "$BACKUP_DIR"
sudo chown azureuser:azureuser "$LOG_DIR" "$BACKUP_DIR"

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" | tee -a "$LOG_FILE" >&2
}

send_slack_alert() {
    local message="$1"
    local emoji="$2"
    
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"${emoji} Harvey Intelligence Engine: ${message}\"}" \
            >> "$LOG_FILE" 2>&1 || true
    fi
}

# Backup current models
backup_models() {
    log "📦 Backing up current models..."
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/backup_$backup_timestamp"
    
    if [ -d "$MODEL_DIR" ]; then
        mkdir -p "$backup_path"
        cp -r "$MODEL_DIR"/*.pkl "$backup_path/" 2>/dev/null || true
        cp -r "$MODEL_DIR"/*.joblib "$backup_path/" 2>/dev/null || true
        log "✅ Models backed up to: $backup_path"
        echo "$backup_path" > "$BACKUP_DIR/latest_backup.txt"
    else
        log "⚠️  Model directory not found: $MODEL_DIR"
    fi
}

# Restore models from backup
rollback_models() {
    log "⏪ Rolling back to previous model version..."
    
    if [ -f "$BACKUP_DIR/latest_backup.txt" ]; then
        local backup_path=$(cat "$BACKUP_DIR/latest_backup.txt")
        
        if [ -d "$backup_path" ]; then
            cp -r "$backup_path"/*.pkl "$MODEL_DIR/" 2>/dev/null || true
            cp -r "$backup_path"/*.joblib "$MODEL_DIR/" 2>/dev/null || true
            log "✅ Models restored from: $backup_path"
            
            # Restart Intelligence Engine
            sudo systemctl restart harvey-intelligence.service || sudo systemctl restart ml-api.service
            log "✅ Intelligence Engine restarted with restored models"
        else
            log_error "Backup path not found: $backup_path"
            return 1
        fi
    else
        log_error "No backup found for rollback"
        return 1
    fi
}

# Cleanup old backups (keep last 7 days)
cleanup_old_backups() {
    log "🧹 Cleaning up old backups (keeping last 7)..."
    
    if [ -d "$BACKUP_DIR" ]; then
        # Keep only the 7 most recent backups
        ls -dt "$BACKUP_DIR"/backup_* 2>/dev/null | tail -n +8 | xargs rm -rf 2>/dev/null || true
        log "✅ Old backups cleaned up"
    fi
}

# Run model training
train_models() {
    log "🚀 Starting model training..."
    
    # Initialize conda for bash
    eval "$($CONDA_BASE/bin/conda shell.bash hook)"
    
    # Activate conda environment
    conda activate "$CONDA_ENV_NAME"
    
    # Verify activation
    if [ "$CONDA_DEFAULT_ENV" != "$CONDA_ENV_NAME" ]; then
        log_error "Failed to activate conda environment: $CONDA_ENV_NAME"
        return 1
    fi
    
    log "✅ Conda environment activated: $CONDA_DEFAULT_ENV"
    
    # Change to scripts directory
    cd "$SCRIPTS_DIR"
    
    # Run training script (adjust based on your actual training script)
    if [ -f "train_all_models.py" ]; then
        python train_all_models.py >> "$LOG_FILE" 2>&1
        log "✅ Training completed successfully"
    elif [ -f "train.py" ]; then
        python train.py >> "$LOG_FILE" 2>&1
        log "✅ Training completed successfully"
    else
        log_error "Training script not found"
        return 1
    fi
}

# Validate new models
validate_models() {
    log "🔍 Validating new models..."
    
    # Initialize conda for bash
    eval "$($CONDA_BASE/bin/conda shell.bash hook)"
    
    # Activate conda environment
    conda activate "$CONDA_ENV_NAME"
    
    # Change to scripts directory
    cd "$SCRIPTS_DIR"
    
    # Run validation script (adjust based on your actual validation script)
    if [ -f "validate_models.py" ]; then
        python validate_models.py >> "$LOG_FILE" 2>&1
        local validation_result=$?
        
        if [ $validation_result -eq 0 ]; then
            log "✅ Model validation passed"
            return 0
        else
            log_error "Model validation failed"
            return 1
        fi
    else
        log "⚠️  No validation script found, skipping validation"
        return 0
    fi
}

# Restart Intelligence Engine to load new models
restart_intelligence_engine() {
    log "🔄 Restarting Intelligence Engine..."
    
    # Try new service name first, fall back to old name
    if sudo systemctl restart harvey-intelligence.service 2>/dev/null; then
        log "✅ harvey-intelligence.service restarted"
    elif sudo systemctl restart ml-api.service 2>/dev/null; then
        log "✅ ml-api.service restarted"
    else
        log_error "Failed to restart Intelligence Engine"
        return 1
    fi
    
    # Wait for service to be ready
    sleep 5
    
    # Test health endpoint
    if curl -s http://127.0.0.1:9000/api/internal/ml/health > /dev/null 2>&1; then
        log "✅ Intelligence Engine is healthy"
        return 0
    else
        log_error "Intelligence Engine health check failed"
        return 1
    fi
}

# Main training workflow
main() {
    log "═══════════════════════════════════════════════════"
    log "🤖 Harvey Intelligence Engine - Daily Training"
    log "═══════════════════════════════════════════════════"
    
    send_slack_alert "Daily model training started" "🚀"
    
    # Step 1: Backup current models
    backup_models
    
    # Step 2: Train new models
    if ! train_models; then
        log_error "Training failed, keeping current models"
        send_slack_alert "Training FAILED - current models unchanged" "❌"
        exit 1
    fi
    
    # Step 3: Validate new models
    if ! validate_models; then
        log_error "Validation failed, rolling back to previous models"
        rollback_models
        send_slack_alert "Validation FAILED - rolled back to previous models" "⚠️"
        exit 1
    fi
    
    # Step 4: Restart Intelligence Engine
    if ! restart_intelligence_engine; then
        log_error "Failed to restart Intelligence Engine, rolling back"
        rollback_models
        send_slack_alert "Restart FAILED - rolled back to previous models" "❌"
        exit 1
    fi
    
    # Step 5: Cleanup old backups
    cleanup_old_backups
    
    # Step 6: Success!
    log "═══════════════════════════════════════════════════"
    log "✅ Daily training completed successfully!"
    log "═══════════════════════════════════════════════════"
    
    send_slack_alert "Daily training completed successfully!" "✅"
    
    # Display log location
    log "📝 Full log: $LOG_FILE"
}

# Handle errors
trap 'log_error "Script failed at line $LINENO"; send_slack_alert "Training script crashed unexpectedly" "💥"; exit 1' ERR

# Run main workflow
main
