"""
Background Job Scheduler Service

Simple in-memory scheduler using threading for:
- Alert condition checking (every 5 minutes)
- Daily digest generation (daily at 8 AM)

No external dependencies (Celery, etc.) needed for MVP.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from sqlalchemy import text

from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler_service")


class BackgroundScheduler:
    """
    Simple background scheduler that runs tasks in a daemon thread.
    
    Features:
    - Alert checking every 5 minutes
    - Daily digest generation at 8 AM
    - Graceful startup/shutdown
    - Error handling and logging
    """
    
    def __init__(self):
        self.running = False
        self.thread = None
        self._last_alert_check = datetime.now()
        self._last_daily_digest = datetime.now()
        
    def start(self):
        """Start background scheduler thread."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("✅ Background scheduler started")
        logger.info("   - Alert checks: Every 5 minutes")
        logger.info("   - Daily digests: 8:00 AM daily")
    
    def _run_scheduler(self):
        """
        Main scheduler loop.
        
        Runs continuously, checking for tasks that need to be executed.
        Uses sleep intervals to avoid CPU spinning.
        """
        logger.info("[scheduler] Scheduler loop started")
        
        while self.running:
            try:
                now = datetime.now()
                
                if (now - self._last_alert_check) >= timedelta(minutes=5):
                    self._check_all_alerts()
                    self._last_alert_check = now
                
                if now.hour == 8 and now.minute < 5:
                    if (now - self._last_daily_digest).days >= 1:
                        self._generate_all_digests()
                        self._last_daily_digest = now
                
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"[scheduler] Error in scheduler loop: {e}", exc_info=True)
                time.sleep(60)
        
        logger.info("[scheduler] Scheduler loop stopped")
    
    def _check_all_alerts(self):
        """
        Check all active alerts for triggering conditions.
        
        Imports alert_service dynamically to avoid circular imports.
        """
        try:
            from app.services.alert_service import check_alert_conditions
            
            logger.info("[scheduler] Checking all active alerts...")
            start_time = time.time()
            
            triggered = check_alert_conditions()
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[scheduler] Alert check complete: {len(triggered)} triggered "
                f"({elapsed_ms}ms)"
            )
            
            if triggered:
                for alert in triggered:
                    logger.info(
                        f"[scheduler] Alert triggered: {alert.get('rule_name')} "
                        f"(event {alert.get('event_id')})"
                    )
                    
        except Exception as e:
            logger.error(f"[scheduler] Alert check failed: {e}", exc_info=True)
    
    def _generate_all_digests(self):
        """
        Generate daily digests for all active sessions.
        
        Active sessions = sessions with activity in the last 7 days.
        """
        try:
            from app.services.insights_service import generate_daily_digest
            
            logger.info("[scheduler] Generating daily digests for active sessions...")
            start_time = time.time()
            
            query = text("""
                SELECT session_id 
                FROM dbo.user_sessions 
                WHERE last_active >= DATEADD(day, -7, GETDATE());
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query)
                sessions = [row[0] for row in result]
            
            logger.info(f"[scheduler] Found {len(sessions)} active sessions")
            
            success_count = 0
            error_count = 0
            
            for session_id in sessions:
                try:
                    result = generate_daily_digest(session_id)
                    
                    if result.get("success"):
                        success_count += 1
                        logger.info(
                            f"[scheduler] Generated digest for {session_id}: "
                            f"{result.get('insight_id')}"
                        )
                    else:
                        logger.info(
                            f"[scheduler] Skipped digest for {session_id}: "
                            f"{result.get('message', 'No data')}"
                        )
                        
                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"[scheduler] Failed to generate digest for {session_id}: {e}"
                    )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[scheduler] Daily digest generation complete: "
                f"{success_count} success, {error_count} errors ({elapsed_ms}ms)"
            )
            
        except Exception as e:
            logger.error(f"[scheduler] Digest generation failed: {e}", exc_info=True)
    
    def stop(self):
        """Stop the scheduler gracefully."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("[scheduler] Stopping background scheduler...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("✅ Background scheduler stopped")
    
    def trigger_alert_check(self):
        """
        Manually trigger an alert check (useful for testing).
        
        This bypasses the normal 5-minute interval.
        """
        logger.info("[scheduler] Manual alert check triggered")
        self._check_all_alerts()
    
    def trigger_digest_generation(self):
        """
        Manually trigger digest generation (useful for testing).
        
        This bypasses the normal daily schedule.
        """
        logger.info("[scheduler] Manual digest generation triggered")
        self._generate_all_digests()


scheduler = BackgroundScheduler()
