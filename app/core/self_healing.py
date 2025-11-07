"""
Self-Healing System for Harvey ML Services
Monitors and automatically recovers from failures
"""

import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque
import subprocess

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "closed"
        
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
    def is_available(self) -> bool:
        """Check if service is available"""
        if self.state == "closed":
            return True
            
        if self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.last_failure_time).seconds
                if time_since_failure >= self.timeout:
                    self.state = "half_open"
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False
            
        return True  # half_open state


class SelfHealingManager:
    """Manages self-healing for all ML services"""
    
    def __init__(self):
        """Initialize self-healing manager"""
        self.circuit_breakers = {
            "ml_api": CircuitBreaker(failure_threshold=5, timeout=60),
            "ml_payout_rating": CircuitBreaker(failure_threshold=3, timeout=30),
            "ml_dividend_calendar": CircuitBreaker(failure_threshold=3, timeout=30),
            "ml_training": CircuitBreaker(failure_threshold=2, timeout=120)
        }
        
        self.recovery_history = deque(maxlen=100)
        self.health_scores = {
            "ml_api": 1.0,
            "ml_payout_rating": 1.0,
            "ml_dividend_calendar": 1.0,
            "ml_training": 1.0
        }
        
        self.recovery_strategies = {
            "ml_api": self._recover_ml_api,
            "ml_payout_rating": self._recover_payout_rating,
            "ml_dividend_calendar": self._recover_dividend_calendar,
            "ml_training": self._recover_ml_training
        }
        
    def check_circuit(self, service_name: str) -> bool:
        """
        Check if circuit allows requests.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if requests allowed, False otherwise
        """
        if service_name in self.circuit_breakers:
            return self.circuit_breakers[service_name].is_available()
        return True
        
    def record_success(self, service_name: str):
        """Record successful operation"""
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name].record_success()
            # Improve health score
            current_score = self.health_scores.get(service_name, 1.0)
            self.health_scores[service_name] = min(1.0, current_score + 0.1)
            
    def record_failure(self, service_name: str, error: str):
        """Record failed operation"""
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name].record_failure()
            # Decrease health score
            current_score = self.health_scores.get(service_name, 1.0)
            self.health_scores[service_name] = max(0.0, current_score - 0.2)
            
        # Log failure
        self.recovery_history.append({
            "service": service_name,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "action": "failure_recorded"
        })
        
    async def attempt_recovery(self, service_name: str):
        """
        Attempt to recover a failed service.
        
        Args:
            service_name: Name of the service to recover
        """
        logger.info(f"Attempting recovery for {service_name}")
        
        if service_name in self.recovery_strategies:
            try:
                success = await self.recovery_strategies[service_name]()
                
                if success:
                    logger.info(f"Successfully recovered {service_name}")
                    self.record_success(service_name)
                    self.recovery_history.append({
                        "service": service_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "recovery_success"
                    })
                else:
                    logger.error(f"Failed to recover {service_name}")
                    self.recovery_history.append({
                        "service": service_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "recovery_failed"
                    })
                    
            except Exception as e:
                logger.error(f"Error during recovery of {service_name}: {e}")
                
    async def _recover_ml_api(self) -> bool:
        """Recover ML API service"""
        try:
            # Try to restart the ML API service on Azure VM
            result = subprocess.run(
                ["ssh", "azureuser@20.81.210.213", "sudo systemctl restart harvey-ml"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Wait for service to start
                await asyncio.sleep(10)
                
                # Test if service is responding
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://20.81.210.213:9000/health")
                    return response.status_code == 200
                    
            return False
            
        except Exception as e:
            logger.error(f"Failed to recover ML API: {e}")
            return False
            
    async def _recover_payout_rating(self) -> bool:
        """Recover payout rating scheduler"""
        try:
            # Restart the payout rating timer
            result = subprocess.run(
                ["ssh", "azureuser@20.81.210.213", 
                 "sudo systemctl restart harvey-payout-rating.timer"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to recover payout rating: {e}")
            return False
            
    async def _recover_dividend_calendar(self) -> bool:
        """Recover dividend calendar scheduler"""
        try:
            # Restart the dividend calendar timer
            result = subprocess.run(
                ["ssh", "azureuser@20.81.210.213",
                 "sudo systemctl restart harvey-dividend-calendar.timer"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to recover dividend calendar: {e}")
            return False
            
    async def _recover_ml_training(self) -> bool:
        """Recover ML training scheduler"""
        try:
            # Restart the ML training timer
            result = subprocess.run(
                ["ssh", "azureuser@20.81.210.213",
                 "sudo systemctl restart harvey-ml-training.timer"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to recover ML training: {e}")
            return False
            
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "overall_health": 0.0,
            "recent_recoveries": []
        }
        
        # Service health
        for service, breaker in self.circuit_breakers.items():
            report["services"][service] = {
                "circuit_state": breaker.state,
                "failure_count": breaker.failure_count,
                "health_score": self.health_scores.get(service, 0.0),
                "available": breaker.is_available()
            }
            
        # Overall health (average of all services)
        if self.health_scores:
            report["overall_health"] = sum(self.health_scores.values()) / len(self.health_scores)
            
        # Recent recoveries
        recent_recoveries = [
            h for h in self.recovery_history 
            if h.get("action") in ["recovery_success", "recovery_failed"]
        ]
        report["recent_recoveries"] = list(recent_recoveries)[-10:]  # Last 10 recoveries
        
        return report
        
    async def monitor_and_heal(self):
        """
        Continuous monitoring and healing loop.
        Should be run as a background task.
        """
        while True:
            try:
                # Check each service
                for service in self.circuit_breakers.keys():
                    # If service health is low, attempt recovery
                    if self.health_scores.get(service, 1.0) < 0.5:
                        if self.check_circuit(service):
                            logger.info(f"Low health score for {service}, attempting recovery")
                            await self.attempt_recovery(service)
                            
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)


# Global instance
self_healing_manager = SelfHealingManager()


def get_self_healing_manager() -> SelfHealingManager:
    """Get global self-healing manager instance"""
    return self_healing_manager