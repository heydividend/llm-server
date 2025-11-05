"""
Admin API Endpoints for Harvey System Management
Provides comprehensive monitoring, logging, and system control.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import logging

from app.core.logging_config import LOG_DIR
from app.middleware.api_logging import log_api_event
from app.services.model_audit_service import ModelAuditService

# Set up admin logger
logger = logging.getLogger("admin_api")

router = APIRouter(prefix="/admin", tags=["Admin"])


# ======================== LOG ENDPOINTS ========================

@router.get("/logs")
async def get_logs(
    log_type: str = Query("api_requests", description="Type of log to retrieve"),
    lines: int = Query(100, description="Number of recent lines to return"),
    filter_text: Optional[str] = Query(None, description="Filter logs containing this text"),
    request_id: Optional[str] = Query(None, description="Filter by specific request ID")
):
    """
    Retrieve recent log entries.
    
    Log types:
    - api_requests: All API requests and responses
    - api_errors: Error logs
    - api_performance: Performance metrics
    - database_queries: Database query logs
    - model_usage: AI model usage and costs
    - harvey_intelligence: Harvey service logs
    - model_audit: Model audit logs
    """
    try:
        # Map log type to file name
        log_files = {
            "api_requests": "api_requests.log",
            "api_errors": "api_errors.log",
            "api_performance": "api_performance.log",
            "database_queries": "database_queries.log",
            "model_usage": "model_usage.log",
            "harvey_intelligence": "harvey_intelligence.log",
            "model_audit": "model_audit_service.log",
            "harvey_main": "harvey_main.log",
        }
        
        if log_type not in log_files:
            raise HTTPException(status_code=400, detail=f"Invalid log type. Choose from: {list(log_files.keys())}")
        
        log_file_path = LOG_DIR / log_files[log_type]
        
        if not log_file_path.exists():
            return {"logs": [], "message": f"Log file not found: {log_files[log_type]}"}
        
        # Read log file
        with open(log_file_path, "r") as f:
            all_lines = f.readlines()
        
        # Apply filters
        filtered_lines = []
        for line in all_lines:
            # Filter by text
            if filter_text and filter_text.lower() not in line.lower():
                continue
            
            # Filter by request ID
            if request_id and request_id not in line:
                continue
            
            filtered_lines.append(line.strip())
        
        # Return recent lines
        recent_lines = filtered_lines[-lines:] if lines > 0 else filtered_lines
        
        # Parse JSON logs if possible
        parsed_logs = []
        for line in recent_lines:
            try:
                # Try to extract JSON from log line
                if "{" in line:
                    json_start = line.index("{")
                    json_str = line[json_start:]
                    parsed_logs.append(json.loads(json_str))
                else:
                    parsed_logs.append({"raw": line})
            except:
                parsed_logs.append({"raw": line})
        
        return {
            "log_type": log_type,
            "total_lines": len(filtered_lines),
            "returned_lines": len(parsed_logs),
            "logs": parsed_logs
        }
        
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/summary")
async def get_logs_summary():
    """
    Get a summary of all available log files with sizes and recent activity.
    """
    try:
        summary = []
        
        for log_file in LOG_DIR.glob("*.log"):
            stats = log_file.stat()
            
            # Get last few lines to check recent activity
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    last_line = lines[-1] if lines else ""
                    total_lines = len(lines)
            except:
                last_line = ""
                total_lines = 0
            
            summary.append({
                "file": log_file.name,
                "size_mb": round(stats.st_size / (1024 * 1024), 2),
                "total_lines": total_lines,
                "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "last_entry_preview": last_line[:200] if last_line else None
            })
        
        return {
            "log_directory": str(LOG_DIR),
            "total_log_files": len(summary),
            "logs": sorted(summary, key=lambda x: x["last_modified"], reverse=True)
        }
        
    except Exception as e:
        logger.error(f"Error getting log summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================== METRICS ENDPOINTS ========================

@router.get("/metrics")
async def get_system_metrics(
    time_range: str = Query("1h", description="Time range: 1h, 6h, 24h, 7d")
):
    """
    Get system performance metrics and statistics.
    """
    try:
        # Parse time range
        time_ranges = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7)
        }
        
        if time_range not in time_ranges:
            raise HTTPException(status_code=400, detail=f"Invalid time range. Choose from: {list(time_ranges.keys())}")
        
        cutoff_time = datetime.utcnow() - time_ranges[time_range]
        
        # Analyze performance logs
        performance_stats = await analyze_performance_logs(cutoff_time)
        
        # Analyze error logs
        error_stats = await analyze_error_logs(cutoff_time)
        
        # Analyze model usage
        model_stats = await analyze_model_usage(cutoff_time)
        
        return {
            "time_range": time_range,
            "period": {
                "from": cutoff_time.isoformat(),
                "to": datetime.utcnow().isoformat()
            },
            "performance": performance_stats,
            "errors": error_stats,
            "model_usage": model_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/endpoints")
async def get_endpoint_metrics():
    """
    Get performance metrics grouped by API endpoint.
    """
    try:
        perf_log_path = LOG_DIR / "api_performance.log"
        
        if not perf_log_path.exists():
            return {"message": "No performance data available"}
        
        endpoint_stats = {}
        
        with open(perf_log_path, "r") as f:
            for line in f:
                try:
                    if "{" in line:
                        json_start = line.index("{")
                        log_entry = json.loads(line[json_start:])
                        
                        path = log_entry.get("path", "unknown")
                        method = log_entry.get("method", "unknown")
                        duration = log_entry.get("duration_ms", 0)
                        status = log_entry.get("status_code", 0)
                        
                        key = f"{method} {path}"
                        
                        if key not in endpoint_stats:
                            endpoint_stats[key] = {
                                "count": 0,
                                "total_duration_ms": 0,
                                "avg_duration_ms": 0,
                                "max_duration_ms": 0,
                                "min_duration_ms": float('inf'),
                                "status_codes": {},
                                "slow_requests": 0
                            }
                        
                        stats = endpoint_stats[key]
                        stats["count"] += 1
                        stats["total_duration_ms"] += duration
                        stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]
                        stats["max_duration_ms"] = max(stats["max_duration_ms"], duration)
                        stats["min_duration_ms"] = min(stats["min_duration_ms"], duration)
                        
                        status_str = str(status)
                        stats["status_codes"][status_str] = stats["status_codes"].get(status_str, 0) + 1
                        
                        if duration > 1000:
                            stats["slow_requests"] += 1
                        
                except:
                    continue
        
        # Sort by request count
        sorted_endpoints = sorted(
            endpoint_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        return {
            "total_endpoints": len(endpoint_stats),
            "endpoints": [
                {
                    "endpoint": endpoint,
                    **stats
                }
                for endpoint, stats in sorted_endpoints[:50]  # Top 50 endpoints
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting endpoint metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================== MODEL AUDIT ENDPOINTS ========================

@router.get("/models/audit")
async def get_model_audit_logs(
    limit: int = Query(100, description="Number of recent entries"),
    model: Optional[str] = Query(None, description="Filter by model name")
):
    """
    Get model audit logs showing which models were used and why.
    """
    try:
        audit_service = ModelAuditService()
        
        # Get recent audit entries
        query = "SELECT TOP (?) * FROM dividend_model_audit_log"
        params = [limit]
        
        if model:
            query = "SELECT TOP (?) * FROM dividend_model_audit_log WHERE model_used = ?"
            params = [limit, model]
        
        query += " ORDER BY timestamp DESC"
        
        # Note: This would normally query the database
        # For now, return mock data or read from audit log file
        
        audit_log_path = LOG_DIR / "model_audit_service.log"
        
        if not audit_log_path.exists():
            return {"message": "No audit data available"}
        
        audit_entries = []
        
        with open(audit_log_path, "r") as f:
            lines = f.readlines()[-limit:]
            for line in reversed(lines):
                try:
                    if "Model selected:" in line or "Audit logged:" in line:
                        audit_entries.append({"log": line.strip()})
                except:
                    continue
        
        return {
            "total_entries": len(audit_entries),
            "audit_logs": audit_entries
        }
        
    except Exception as e:
        logger.error(f"Error getting model audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/usage")
async def get_model_usage_stats():
    """
    Get aggregated model usage statistics and costs.
    """
    try:
        usage_log_path = LOG_DIR / "model_usage.log"
        
        if not usage_log_path.exists():
            return {"message": "No model usage data available"}
        
        model_stats = {}
        total_cost = 0
        total_tokens = 0
        
        with open(usage_log_path, "r") as f:
            for line in f:
                try:
                    if "{" in line:
                        json_start = line.index("{")
                        log_entry = json.loads(line[json_start:])
                        
                        model = log_entry.get("model", "unknown")
                        tokens = log_entry.get("tokens", 0)
                        cost = log_entry.get("cost_usd", 0)
                        
                        if model not in model_stats:
                            model_stats[model] = {
                                "request_count": 0,
                                "total_tokens": 0,
                                "total_cost_usd": 0
                            }
                        
                        model_stats[model]["request_count"] += 1
                        model_stats[model]["total_tokens"] += tokens
                        model_stats[model]["total_cost_usd"] += cost
                        
                        total_cost += cost
                        total_tokens += tokens
                        
                except:
                    continue
        
        return {
            "total_cost_usd": round(total_cost, 2),
            "total_tokens": total_tokens,
            "models": model_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting model usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================== SYSTEM STATUS ENDPOINTS ========================

@router.get("/status")
async def get_admin_status():
    """
    Get comprehensive system status for admin dashboard.
    """
    try:
        from app.services.harvey_intelligence import harvey
        
        # Get Harvey status
        harvey_status = harvey.get_system_status()
        
        # Check database connection
        try:
            from app.database.connection import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                db_status = "connected"
        except:
            db_status = "disconnected"
        
        # Check ML API connection
        ml_api_status = "connected" if os.getenv("ML_API_BASE_URL") else "not configured"
        
        # Get service statuses
        services = {
            "harvey_intelligence": harvey_status.get("status", "unknown"),
            "database": db_status,
            "ml_api": ml_api_status,
            "azure_openai": "connected" if os.getenv("AZURE_OPENAI_ENDPOINT") else "not configured",
            "logging": "active",
            "scheduler": "active",  # Would check actual scheduler status
        }
        
        # Get recent errors count
        error_count = await count_recent_errors(timedelta(hours=1))
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "services": services,
            "recent_errors": error_count,
            "harvey_details": harvey_status
        }
        
    except Exception as e:
        logger.error(f"Error getting admin status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    cache_type: str = Query(..., description="Cache type: all, ml, query, dividend")
):
    """
    Clear specific cache types.
    """
    try:
        cleared = []
        
        if cache_type in ["all", "ml"]:
            from app.services.ml_cache import ml_cache
            ml_cache.clear()
            cleared.append("ml_cache")
        
        if cache_type in ["all", "query"]:
            from app.services.query_cache import query_cache
            query_cache.clear()
            cleared.append("query_cache")
        
        if cache_type in ["all", "dividend"]:
            from app.services.dividend_context_service import DividendContextService
            service = DividendContextService()
            service.cache.clear()
            cleared.append("dividend_cache")
        
        log_api_event("cache_cleared", {"cache_type": cache_type, "cleared": cleared})
        
        return {
            "status": "success",
            "cleared": cleared,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================== HELPER FUNCTIONS ========================

async def analyze_performance_logs(cutoff_time: datetime) -> Dict[str, Any]:
    """Analyze performance logs for the given time period."""
    perf_log_path = LOG_DIR / "api_performance.log"
    
    if not perf_log_path.exists():
        return {}
    
    request_count = 0
    total_duration = 0
    slow_requests = 0
    
    with open(perf_log_path, "r") as f:
        for line in f:
            try:
                if "{" in line:
                    json_start = line.index("{")
                    log_entry = json.loads(line[json_start:])
                    
                    timestamp = datetime.fromisoformat(log_entry.get("timestamp", ""))
                    if timestamp < cutoff_time:
                        continue
                    
                    request_count += 1
                    total_duration += log_entry.get("duration_ms", 0)
                    
                    if log_entry.get("slow_request", False):
                        slow_requests += 1
                        
            except:
                continue
    
    avg_duration = total_duration / request_count if request_count > 0 else 0
    
    return {
        "total_requests": request_count,
        "avg_response_time_ms": round(avg_duration, 2),
        "slow_requests": slow_requests,
        "slow_request_percentage": round((slow_requests / request_count * 100) if request_count > 0 else 0, 2)
    }


async def analyze_error_logs(cutoff_time: datetime) -> Dict[str, Any]:
    """Analyze error logs for the given time period."""
    error_log_path = LOG_DIR / "api_errors.log"
    
    if not error_log_path.exists():
        return {}
    
    error_count = 0
    error_types = {}
    
    with open(error_log_path, "r") as f:
        for line in f:
            try:
                if "{" in line:
                    json_start = line.index("{")
                    log_entry = json.loads(line[json_start:])
                    
                    timestamp = datetime.fromisoformat(log_entry.get("timestamp", ""))
                    if timestamp < cutoff_time:
                        continue
                    
                    error_count += 1
                    error_type = log_entry.get("error_type", "unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                    
            except:
                continue
    
    return {
        "total_errors": error_count,
        "error_types": error_types
    }


async def analyze_model_usage(cutoff_time: datetime) -> Dict[str, Any]:
    """Analyze model usage for the given time period."""
    usage_log_path = LOG_DIR / "model_usage.log"
    
    if not usage_log_path.exists():
        return {}
    
    total_cost = 0
    total_tokens = 0
    model_counts = {}
    
    with open(usage_log_path, "r") as f:
        for line in f:
            try:
                if "{" in line:
                    json_start = line.index("{")
                    log_entry = json.loads(line[json_start:])
                    
                    timestamp = datetime.fromisoformat(log_entry.get("timestamp", ""))
                    if timestamp < cutoff_time:
                        continue
                    
                    total_cost += log_entry.get("cost_usd", 0)
                    total_tokens += log_entry.get("tokens", 0)
                    
                    model = log_entry.get("model", "unknown")
                    model_counts[model] = model_counts.get(model, 0) + 1
                    
            except:
                continue
    
    return {
        "total_cost_usd": round(total_cost, 4),
        "total_tokens": total_tokens,
        "model_usage": model_counts
    }


async def count_recent_errors(time_delta: timedelta) -> int:
    """Count errors in the recent time period."""
    error_log_path = LOG_DIR / "api_errors.log"
    
    if not error_log_path.exists():
        return 0
    
    cutoff_time = datetime.utcnow() - time_delta
    error_count = 0
    
    with open(error_log_path, "r") as f:
        for line in f:
            try:
                if "{" in line:
                    json_start = line.index("{")
                    log_entry = json.loads(line[json_start:])
                    
                    timestamp = datetime.fromisoformat(log_entry.get("timestamp", ""))
                    if timestamp >= cutoff_time:
                        error_count += 1
                        
            except:
                continue
    
    return error_count