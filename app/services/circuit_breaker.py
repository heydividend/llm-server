"""
Circuit Breaker Pattern for ML API Rate Limit Protection

Implements circuit breaker to protect against rate limit errors and API failures:
- CLOSED: Normal operation
- OPEN: Failing - return cached data or fail fast
- HALF_OPEN: Testing recovery

Features:
- Track consecutive failures
- Auto-recovery after timeout
- Fail fast when circuit is OPEN
- Request queuing to prevent rate limit bursts
"""

import time
import logging
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
import threading

logger = logging.getLogger("circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing - reject requests
    HALF_OPEN = "half_open" # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for ML API calls.
    
    Protects against cascading failures and rate limit errors.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self._lock = threading.Lock()
        
        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, recovery={recovery_timeout}s")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is OPEN or function fails
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    logger.info("Circuit breaker: Attempting recovery (HALF_OPEN)")
                    self.state = CircuitState.HALF_OPEN
                else:
                    elapsed = time.time() - (self.last_failure_time or 0)
                    remaining = self.recovery_timeout - elapsed
                    logger.warning(f"Circuit breaker OPEN: Failing fast (retry in {remaining:.0f}s)")
                    raise Exception(f"Circuit breaker is OPEN. Service temporarily unavailable. Retry in {remaining:.0f}s.")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker: Recovery successful (CLOSED)")
                self.state = CircuitState.CLOSED
            
            self.failure_count = 0
            self.last_failure_time = None
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    logger.warning(f"Circuit breaker OPEN: {self.failure_count} consecutive failures")
                    self.state = CircuitState.OPEN
            
            elif self.state == CircuitState.HALF_OPEN:
                logger.warning("Circuit breaker: Recovery failed, reopening circuit")
                self.state = CircuitState.OPEN
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def reset(self):
        """Manually reset circuit breaker."""
        with self._lock:
            logger.info("Circuit breaker: Manual reset")
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED


class RateLimitQueue:
    """
    Request queue to prevent rate limit bursts.
    
    Ensures minimum delay between requests to avoid rate limiting.
    """
    
    def __init__(self, min_interval_seconds: float = 0.1):
        """
        Initialize rate limit queue.
        
        Args:
            min_interval_seconds: Minimum seconds between requests
        """
        self.min_interval = min_interval_seconds
        self.last_request_time: Optional[float] = None
        self._lock = threading.Lock()
        
        logger.info(f"Rate limit queue initialized: min_interval={min_interval_seconds}s")
    
    def wait_if_needed(self):
        """Wait if necessary to maintain rate limit."""
        with self._lock:
            if self.last_request_time is not None:
                elapsed = time.time() - self.last_request_time
                if elapsed < self.min_interval:
                    wait_time = self.min_interval - elapsed
                    logger.debug(f"Rate limiting: waiting {wait_time:.3f}s")
                    time.sleep(wait_time)
            
            self.last_request_time = time.time()


# Global circuit breaker instance for ML API
_ml_circuit_breaker: Optional[CircuitBreaker] = None
_ml_rate_limiter: Optional[RateLimitQueue] = None


def get_ml_circuit_breaker() -> CircuitBreaker:
    """Get or create global ML API circuit breaker."""
    global _ml_circuit_breaker
    if _ml_circuit_breaker is None:
        _ml_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
    return _ml_circuit_breaker


def get_ml_rate_limiter() -> RateLimitQueue:
    """Get or create global ML API rate limiter."""
    global _ml_rate_limiter
    if _ml_rate_limiter is None:
        _ml_rate_limiter = RateLimitQueue(min_interval_seconds=0.1)
    return _ml_rate_limiter
