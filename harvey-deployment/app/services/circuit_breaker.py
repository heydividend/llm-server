"""
Circuit Breaker Pattern for ML API Rate Limit Protection

Implements circuit breaker to protect against rate limit errors and API failures:
- CLOSED: Normal operation
- OPEN: Failing - return cached data or fail fast
- HALF_OPEN: Testing recovery

Features:
- Track consecutive failures
- Exponential backoff with jitter for recovery
- Fail fast when circuit is OPEN
- Request queuing to prevent rate limit bursts
- Configurable recovery attempts in HALF_OPEN state
"""

import time
import logging
import random
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
    Circuit breaker for ML API calls with exponential backoff and jitter.
    
    Protects against cascading failures and rate limit errors.
    Implements intelligent recovery with exponential backoff and jitter.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        initial_recovery_timeout: int = 10,
        max_recovery_timeout: int = 300,
        half_open_max_attempts: int = 3,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker with exponential backoff.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            initial_recovery_timeout: Initial recovery timeout (10s)
            max_recovery_timeout: Maximum recovery timeout (300s = 5 minutes)
            half_open_max_attempts: Maximum recovery attempts in HALF_OPEN state
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.initial_recovery_timeout = initial_recovery_timeout
        self.max_recovery_timeout = max_recovery_timeout
        self.half_open_max_attempts = half_open_max_attempts
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.half_open_attempts = 0
        self.consecutive_open_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self._lock = threading.Lock()
        
        logger.info(
            f"Circuit breaker initialized: threshold={failure_threshold}, "
            f"initial_timeout={initial_recovery_timeout}s, max_timeout={max_recovery_timeout}s, "
            f"half_open_attempts={half_open_max_attempts}"
        )
    
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
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(f"[{timestamp}] Circuit breaker: Attempting recovery (HALF_OPEN) - Attempt {self.half_open_attempts + 1}/{self.half_open_max_attempts}")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_attempts += 1
                else:
                    elapsed = time.time() - (self.last_failure_time or 0)
                    current_timeout = self._get_current_recovery_timeout()
                    remaining = current_timeout - elapsed
                    logger.warning(f"Circuit breaker OPEN: Failing fast (retry in {remaining:.0f}s)")
                    raise Exception(f"Circuit breaker is OPEN. Service temporarily unavailable. Retry in {remaining:.0f}s.")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _get_current_recovery_timeout(self) -> int:
        """
        Calculate current recovery timeout with exponential backoff and jitter.
        
        Exponential backoff: 10s, 20s, 40s, 80s, 160s, 300s (max)
        Jitter: +/- 20% randomness to prevent thundering herd
        """
        base_timeout = min(
            self.initial_recovery_timeout * (2 ** self.consecutive_open_count),
            self.max_recovery_timeout
        )
        
        jitter_range = base_timeout * 0.2
        jitter = random.uniform(-jitter_range, jitter_range)
        
        return int(base_timeout + jitter)
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        
        current_timeout = self._get_current_recovery_timeout()
        elapsed = time.time() - self.last_failure_time
        
        return elapsed >= current_timeout
    
    def _on_success(self):
        """Handle successful call - reset all counters on success."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"[{timestamp}] ✅ Circuit breaker: Recovery successful! Returning to CLOSED state")
                self.state = CircuitState.CLOSED
            
            self.failure_count = 0
            self.half_open_attempts = 0
            self.consecutive_open_count = 0
            self.last_failure_time = None
    
    def _on_failure(self):
        """Handle failed call - implement progressive backoff."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    logger.warning(f"[{timestamp}] Circuit breaker OPEN: {self.failure_count} consecutive failures")
                    self.state = CircuitState.OPEN
                    self.consecutive_open_count = 0
            
            elif self.state == CircuitState.HALF_OPEN:
                if self.half_open_attempts < self.half_open_max_attempts:
                    logger.warning(
                        f"[{timestamp}] Circuit breaker: Recovery attempt {self.half_open_attempts}/{self.half_open_max_attempts} failed, "
                        f"will retry after backoff"
                    )
                    self.state = CircuitState.OPEN
                else:
                    logger.warning(
                        f"[{timestamp}] Circuit breaker: All {self.half_open_max_attempts} recovery attempts exhausted, "
                        f"increasing backoff (attempt #{self.consecutive_open_count + 1})"
                    )
                    self.state = CircuitState.OPEN
                    self.consecutive_open_count += 1
                    self.half_open_attempts = 0
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[{timestamp}] Circuit breaker: Manual reset to CLOSED state")
            self.failure_count = 0
            self.half_open_attempts = 0
            self.consecutive_open_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics for monitoring."""
        with self._lock:
            current_timeout = self._get_current_recovery_timeout() if self.state == CircuitState.OPEN else 0
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "half_open_attempts": self.half_open_attempts,
                "consecutive_open_count": self.consecutive_open_count,
                "current_recovery_timeout": current_timeout,
                "last_failure_time": datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None
            }


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
    """Get or create global ML API circuit breaker with exponential backoff."""
    global _ml_circuit_breaker
    if _ml_circuit_breaker is None:
        _ml_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            initial_recovery_timeout=10,
            max_recovery_timeout=300,
            half_open_max_attempts=3,
            expected_exception=Exception
        )
    return _ml_circuit_breaker


def get_ml_rate_limiter() -> RateLimitQueue:
    """Get or create global ML API rate limiter."""
    global _ml_rate_limiter
    if _ml_rate_limiter is None:
        _ml_rate_limiter = RateLimitQueue(min_interval_seconds=0.1)
    return _ml_rate_limiter
