"""
Comprehensive API Logging Middleware
Logs all API requests, responses, errors, and performance metrics.
"""

import time
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import traceback

from app.core.logging_config import setup_logger

# Set up dedicated API logger
api_logger = setup_logger("api_requests", logging.INFO, "api_requests.log")
error_logger = setup_logger("api_errors", logging.ERROR, "api_errors.log")
performance_logger = setup_logger("api_performance", logging.INFO, "api_performance.log")


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests, responses, and errors.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_paths = {"/health", "/metrics", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Capture request details
        start_time = time.time()
        request_body = None
        
        # Try to read request body (for POST/PUT/PATCH)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                request_body = body_bytes.decode("utf-8")
                # Recreate request with body for downstream processing
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception as e:
                request_body = f"Error reading body: {str(e)}"
        
        # Log request
        request_log = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "body": request_body[:1000] if request_body else None,  # Limit body size in logs
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        api_logger.info(f"[{request_id}] REQUEST: {json.dumps(request_log, default=str)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Capture response
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            response_log = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "headers": dict(response.headers),
            }
            
            api_logger.info(f"[{request_id}] RESPONSE: {json.dumps(response_log, default=str)}")
            
            # Log performance metrics
            performance_log = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "slow_request": duration_ms > 1000,  # Flag requests over 1 second
            }
            
            performance_logger.info(json.dumps(performance_log, default=str))
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time-MS"] = str(round(duration_ms, 2))
            
            return response
            
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            
            error_log = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "duration_ms": round(duration_ms, 2),
            }
            
            error_logger.error(f"[{request_id}] ERROR: {json.dumps(error_log, default=str)}")
            
            # Re-raise the exception
            raise


class QueryLoggingMiddleware:
    """
    Middleware to log database queries and their performance.
    """
    
    def __init__(self):
        self.query_logger = setup_logger("database_queries", logging.INFO, "database_queries.log")
    
    def log_query(self, query: str, params: Dict[str, Any], duration_ms: float, 
                  request_id: Optional[str] = None):
        """Log a database query with performance metrics."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query[:500],  # Limit query length
            "params": str(params)[:200] if params else None,
            "duration_ms": round(duration_ms, 2),
            "slow_query": duration_ms > 100,  # Flag queries over 100ms
        }
        
        self.query_logger.info(json.dumps(log_entry, default=str))


# Global query logger instance
query_logger = QueryLoggingMiddleware()


def log_api_event(event_type: str, data: Dict[str, Any], request_id: Optional[str] = None):
    """
    Helper function to log custom API events.
    
    Args:
        event_type: Type of event (e.g., "model_routing", "cache_hit", "ml_api_call")
        data: Event data to log
        request_id: Optional request ID for correlation
    """
    event_logger = setup_logger("api_events", logging.INFO, "api_events.log")
    
    log_entry = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data,
    }
    
    event_logger.info(json.dumps(log_entry, default=str))


def log_model_usage(model_name: str, tokens_used: int, cost: float, 
                   request_id: Optional[str] = None):
    """
    Log AI model usage for cost tracking.
    
    Args:
        model_name: Name of the AI model used
        tokens_used: Number of tokens consumed
        cost: Estimated cost in USD
        request_id: Optional request ID for correlation
    """
    model_logger = setup_logger("model_usage", logging.INFO, "model_usage.log")
    
    log_entry = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "model": model_name,
        "tokens": tokens_used,
        "cost_usd": round(cost, 4),
    }
    
    model_logger.info(json.dumps(log_entry, default=str))