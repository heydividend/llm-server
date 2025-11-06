"""
Enhanced Logging Service for Harvey
Provides centralized logging for all Harvey operations with tracking and analytics.
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from app.core.logging_config import setup_logger


class EnhancedLoggingService:
    """
    Centralized logging service with enhanced tracking capabilities.
    """
    
    def __init__(self):
        # Set up specialized loggers
        self.api_logger = setup_logger("api_requests", logging.INFO, "api_requests.log")
        self.query_logger = setup_logger("database_queries", logging.INFO, "database_queries.log")
        self.model_logger = setup_logger("model_usage", logging.INFO, "model_usage.log")
        self.event_logger = setup_logger("api_events", logging.INFO, "api_events.log")
        self.error_logger = setup_logger("api_errors", logging.ERROR, "api_errors.log")
        self.dividend_logger = setup_logger("dividend_operations", logging.INFO, "dividend_operations.log")
        self.etf_logger = setup_logger("etf_provider", logging.INFO, "etf_provider.log")
        
    def log_api_request(self, request_id: str, method: str, path: str, 
                        body: Optional[Dict] = None, headers: Optional[Dict] = None):
        """Log incoming API request."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "body": body[:1000] if body else None,  # Limit body size
            "headers": headers
        }
        self.api_logger.info(json.dumps(log_entry, default=str))
    
    def log_api_response(self, request_id: str, status_code: int, 
                        duration_ms: float, response_size: int = 0):
        """Log API response."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "response_size_bytes": response_size,
            "slow_request": duration_ms > 1000
        }
        self.api_logger.info(json.dumps(log_entry, default=str))
    
    def log_database_query(self, query: str, params: Optional[Dict] = None,
                          duration_ms: float = 0, rows_affected: int = 0,
                          request_id: Optional[str] = None):
        """Log database query with performance metrics."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query[:500],  # Limit query length
            "params": str(params)[:200] if params else None,
            "duration_ms": round(duration_ms, 2),
            "rows_affected": rows_affected,
            "slow_query": duration_ms > 100
        }
        self.query_logger.info(json.dumps(log_entry, default=str))
    
    def log_model_usage(self, model_name: str, query: str, tokens: int,
                       cost_usd: float, response_time_ms: float,
                       request_id: Optional[str] = None):
        """Log AI model usage with cost tracking."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_name,
            "query_preview": query[:200] if query else None,
            "tokens": tokens,
            "cost_usd": round(cost_usd, 6),
            "response_time_ms": round(response_time_ms, 2),
            "cost_per_token": round(cost_usd / tokens, 8) if tokens > 0 else 0
        }
        self.model_logger.info(json.dumps(log_entry, default=str))
    
    def log_dividend_operation(self, operation: str, symbol: str,
                               data: Dict[str, Any], request_id: Optional[str] = None):
        """Log dividend-specific operations."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "symbol": symbol,
            "data": data
        }
        self.dividend_logger.info(json.dumps(log_entry, default=str))
    
    def log_etf_provider_query(self, provider: str, etf_count: int,
                               query_type: str, request_id: Optional[str] = None):
        """Log ETF provider queries."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "etf_count": etf_count,
            "query_type": query_type
        }
        self.etf_logger.info(json.dumps(log_entry, default=str))
    
    def log_error(self, error: Exception, context: Dict[str, Any],
                 request_id: Optional[str] = None):
        """Log errors with full context."""
        import traceback
        
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        self.error_logger.error(json.dumps(log_entry, default=str))
    
    def log_event(self, event_type: str, data: Dict[str, Any],
                 request_id: Optional[str] = None):
        """Log custom events."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.event_logger.info(json.dumps(log_entry, default=str))
    
    @contextmanager
    def track_operation(self, operation_name: str, request_id: Optional[str] = None):
        """
        Context manager to track operation timing.
        
        Usage:
            with logger.track_operation("fetch_dividends", request_id):
                # Your operation here
                pass
        """
        start_time = time.time()
        
        self.log_event("operation_started", {
            "operation": operation_name,
            "start_time": datetime.utcnow().isoformat()
        }, request_id)
        
        try:
            yield
            
            duration_ms = (time.time() - start_time) * 1000
            self.log_event("operation_completed", {
                "operation": operation_name,
                "duration_ms": round(duration_ms, 2),
                "status": "success"
            }, request_id)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_error(e, {
                "operation": operation_name,
                "duration_ms": round(duration_ms, 2)
            }, request_id)
            raise
    
    def get_request_logs(self, request_id: str) -> List[Dict]:
        """
        Retrieve all logs for a specific request ID.
        """
        logs = []
        
        # Search through all log files for the request ID
        log_files = [
            "api_requests.log",
            "api_errors.log",
            "database_queries.log",
            "model_usage.log",
            "api_events.log",
            "dividend_operations.log",
            "etf_provider.log"
        ]
        
        from app.core.logging_config import LOG_DIR
        
        for log_file in log_files:
            log_path = LOG_DIR / log_file
            if log_path.exists():
                with open(log_path, "r") as f:
                    for line in f:
                        if request_id in line:
                            try:
                                if "{" in line:
                                    json_start = line.index("{")
                                    log_entry = json.loads(line[json_start:])
                                    log_entry["source"] = log_file
                                    logs.append(log_entry)
                            except:
                                logs.append({"raw": line.strip(), "source": log_file})
        
        # Sort by timestamp
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=False)
        
        return logs


# Global instance
enhanced_logger = EnhancedLoggingService()


# Convenience functions
def log_api_request(*args, **kwargs):
    enhanced_logger.log_api_request(*args, **kwargs)

def log_api_response(*args, **kwargs):
    enhanced_logger.log_api_response(*args, **kwargs)

def log_database_query(*args, **kwargs):
    enhanced_logger.log_database_query(*args, **kwargs)

def log_model_usage(*args, **kwargs):
    enhanced_logger.log_model_usage(*args, **kwargs)

def log_dividend_operation(*args, **kwargs):
    enhanced_logger.log_dividend_operation(*args, **kwargs)

def log_etf_provider_query(*args, **kwargs):
    enhanced_logger.log_etf_provider_query(*args, **kwargs)

def log_error(*args, **kwargs):
    enhanced_logger.log_error(*args, **kwargs)

def log_event(*args, **kwargs):
    enhanced_logger.log_event(*args, **kwargs)

def track_operation(*args, **kwargs):
    return enhanced_logger.track_operation(*args, **kwargs)