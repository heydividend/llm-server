"""
ML API Health Monitor

Background health monitoring service that:
- Checks ML API health every 30 seconds
- Detects service recovery and triggers auto-healing
- Resets circuit breaker when service is healthy
- Triggers cache prewarming after recovery
- Tracks uptime/downtime metrics
- Logs all health status changes
"""

import time
import logging
import threading
import httpx
from typing import Optional
from datetime import datetime, timedelta
from app.services.circuit_breaker import get_ml_circuit_breaker, CircuitState

logger = logging.getLogger("ml_health_monitor")


class MLHealthMonitor:
    """
    Background health monitor for ML API with auto-recovery.
    
    Continuously monitors ML API health and triggers self-healing
    when service recovers from failures.
    """
    
    def __init__(
        self,
        health_check_interval: int = 30,
        health_check_timeout: int = 5,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize ML API health monitor.
        
        Args:
            health_check_interval: Seconds between health checks (default: 30)
            health_check_timeout: Health check request timeout (default: 5)
            api_key: ML API key (from environment if not provided)
            base_url: ML API base URL (from environment if not provided)
        """
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        self.health_check_interval = health_check_interval
        self.health_check_timeout = health_check_timeout
        self.api_key = api_key or os.getenv("INTERNAL_ML_API_KEY")
        self.base_url = (base_url or os.getenv("ML_API_BASE_URL") or 
                        "https://2657f601-b8fe-40bd-8b9b-bdce950dabad-00-3ihusjg16z2it.janeway.replit.dev/api/internal/ml")
        
        self.is_running = False
        self.is_healthy = False
        self.last_health_check_time: Optional[float] = None
        self.last_health_status: Optional[bool] = None
        self.total_checks = 0
        self.successful_checks = 0
        self.failed_checks = 0
        self.last_recovery_time: Optional[float] = None
        self.downtime_start: Optional[float] = None
        self.total_downtime_seconds = 0.0
        
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info(
            f"ML Health Monitor initialized: interval={health_check_interval}s, "
            f"timeout={health_check_timeout}s, base_url={self.base_url}"
        )
    
    def start(self):
        """Start background health monitoring."""
        if self.is_running:
            logger.warning("ML Health Monitor already running")
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        logger.info("✅ ML Health Monitor started in background")
    
    def stop(self):
        """Stop background health monitoring."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("ML Health Monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop - runs continuously in background."""
        logger.info("ML Health Monitor: Starting health check loop...")
        
        while self.is_running:
            try:
                # Perform health check
                is_healthy = self._perform_health_check()
                
                # Update state
                with self._lock:
                    self.last_health_check_time = time.time()
                    self.total_checks += 1
                    
                    if is_healthy:
                        self.successful_checks += 1
                    else:
                        self.failed_checks += 1
                    
                    # Detect state transitions
                    if self.last_health_status is not None and self.last_health_status != is_healthy:
                        self._handle_health_status_change(is_healthy)
                    
                    self.last_health_status = is_healthy
                    self.is_healthy = is_healthy
                
                # Sleep until next check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"ML Health Monitor: Error in monitoring loop: {e}", exc_info=True)
                time.sleep(self.health_check_interval)
    
    def _perform_health_check(self) -> bool:
        """
        Perform lightweight health check on ML API.
        
        Uses a simple endpoint to check if service is responding.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Use a lightweight endpoint for health check
            # Try the /health endpoint or insights with a simple ticker
            health_url = f"{self.base_url}/health"
            
            headers = {}
            if self.api_key:
                headers["X-Internal-API-Key"] = self.api_key
            
            with httpx.Client(timeout=self.health_check_timeout) as client:
                response = client.get(health_url, headers=headers)
                
                is_healthy = response.status_code == 200
                
                if is_healthy:
                    logger.debug("ML Health Monitor: ✅ Service healthy")
                else:
                    logger.debug(f"ML Health Monitor: ❌ Service unhealthy (status: {response.status_code})")
                
                return is_healthy
                
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError) as e:
            logger.debug(f"ML Health Monitor: ❌ Service unreachable: {type(e).__name__}")
            return False
        except Exception as e:
            logger.error(f"ML Health Monitor: Health check error: {e}")
            return False
    
    def _handle_health_status_change(self, is_healthy: bool):
        """
        Handle health status transitions and trigger auto-recovery.
        
        Args:
            is_healthy: Current health status
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if is_healthy:
            # Service recovered: DOWN → UP
            logger.info(f"🎉 [{timestamp}] ML API SERVICE RECOVERED! Service is now healthy")
            
            # Calculate downtime
            if self.downtime_start:
                downtime_duration = time.time() - self.downtime_start
                self.total_downtime_seconds += downtime_duration
                logger.info(f"   Downtime duration: {downtime_duration:.1f} seconds")
                self.downtime_start = None
            
            # Trigger auto-recovery
            self._trigger_auto_recovery()
            
            self.last_recovery_time = time.time()
            
        else:
            # Service went down: UP → DOWN
            logger.warning(f"⚠️ [{timestamp}] ML API SERVICE DOWN! Service became unhealthy")
            self.downtime_start = time.time()
    
    def _trigger_auto_recovery(self):
        """
        Trigger automatic recovery actions when service becomes healthy.
        
        Actions:
        1. Reset circuit breaker to CLOSED state
        2. Trigger cache prewarming
        3. Log recovery notification
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Reset circuit breaker
            circuit_breaker = get_ml_circuit_breaker()
            if circuit_breaker.get_state() != CircuitState.CLOSED:
                logger.info(f"[{timestamp}] 🔄 Auto-recovery: Resetting circuit breaker to CLOSED state")
                circuit_breaker.reset()
                logger.info(f"[{timestamp}] ✅ Auto-recovery: Circuit breaker reset successful")
            else:
                logger.info(f"[{timestamp}] ℹ️ Auto-recovery: Circuit breaker already CLOSED")
            
            # Trigger cache prewarming
            logger.info(f"[{timestamp}] 🔄 Auto-recovery: Triggering cache prewarming...")
            self._trigger_cache_prewarming()
            
            logger.info(f"[{timestamp}] ✅ AUTO-RECOVERY COMPLETE: ML API service fully restored")
            
        except Exception as e:
            logger.error(f"[{timestamp}] ❌ Auto-recovery failed: {e}", exc_info=True)
    
    def _trigger_cache_prewarming(self):
        """Trigger cache prewarming after service recovery."""
        try:
            from app.services.cache_prewarmer import get_cache_prewarmer
            import asyncio
            
            prewarmer = get_cache_prewarmer()
            
            # Run prewarming asynchronously in background
            asyncio.run(prewarmer._run_prewarm_tasks())
            
            logger.info("✅ Cache prewarming completed after service recovery")
            
        except Exception as e:
            logger.warning(f"Cache prewarming failed (non-critical): {e}")
    
    def get_health_status(self) -> dict:
        """
        Get current health status and metrics.
        
        Returns:
            Dictionary with health metrics
        """
        with self._lock:
            uptime_percentage = (self.successful_checks / self.total_checks * 100) if self.total_checks > 0 else 0
            
            return {
                "is_healthy": self.is_healthy,
                "last_check_time": datetime.fromtimestamp(self.last_health_check_time).isoformat() if self.last_health_check_time else None,
                "total_checks": self.total_checks,
                "successful_checks": self.successful_checks,
                "failed_checks": self.failed_checks,
                "uptime_percentage": round(uptime_percentage, 2),
                "total_downtime_seconds": round(self.total_downtime_seconds, 1),
                "last_recovery_time": datetime.fromtimestamp(self.last_recovery_time).isoformat() if self.last_recovery_time else None,
                "currently_down": self.downtime_start is not None,
                "current_downtime_seconds": round(time.time() - self.downtime_start, 1) if self.downtime_start else 0
            }


# Global health monitor instance
_ml_health_monitor: Optional[MLHealthMonitor] = None


def get_ml_health_monitor() -> MLHealthMonitor:
    """Get or create global ML health monitor instance."""
    global _ml_health_monitor
    if _ml_health_monitor is None:
        _ml_health_monitor = MLHealthMonitor(
            health_check_interval=30,
            health_check_timeout=5
        )
    return _ml_health_monitor
