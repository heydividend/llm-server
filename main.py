import os
import time
import uuid
import logging
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from sqlalchemy import text

# Import centralized logging configuration FIRST
from app.core.logging_config import get_logger, setup_all_loggers

from app.routes import chat as ai_routes
from app.routes import income_ladder
from app.routes import tax_optimization
from app.routes import alerts
from app.routes import insights
from app.routes import azure_vm
from app.routes import feedback
from app.routes import harvey_status
from app.routes import dividend_strategies
from app.routes import training
from app.routes import admin  # Admin endpoints for logging and monitoring
# from app.routes import ml_schedulers  # ML scheduler endpoints - temporarily disabled due to aiohttp dependency
from app.routers import data_quality
from app.middleware.api_logging import APILoggingMiddleware
from app.core.database import engine
from app.core.auth import verify_api_key
from app.services.scheduler_service import scheduler
from financial_models.api.endpoints import router as financial_router

# Import new feature routes
from app.api.routes import video_routes
from app.api.routes import dividend_lists_routes
from app.api.routes import hashtag_routes


# Setup logging using centralized configuration
setup_all_loggers()
logger = get_logger("harvey")

# Initialize FastAPI
app = FastAPI(title="Chat + SQL Server (Streaming) + Enhanced Web Search")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# Timing Middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = str(uuid.uuid4())[:8]
        request.state.rid = rid
        start = time.time()

        response = await call_next(request)

        elapsed_ms = int((time.time() - start) * 1000)
        logger.info(f"[{rid}] {request.method} {request.url.path} done in {elapsed_ms} ms")

        return response


# Feature Monitoring Middleware - tracks metrics for new features
class FeatureMonitoringMiddleware(BaseHTTPMiddleware):
    """Lightweight middleware to monitor new feature endpoints"""
    
    FEATURE_ENDPOINTS = {
        "/api/videos": "VIDEO_SERVICE",
        "/api/dividend-lists": "DIVIDEND_LISTS",
        "/api/hashtags": "HASHTAG_ANALYTICS"
    }
    
    async def dispatch(self, request, call_next):
        path = request.url.path
        
        # Check if this is a monitored feature endpoint
        feature_name = None
        for prefix, name in self.FEATURE_ENDPOINTS.items():
            if path.startswith(prefix):
                feature_name = name
                break
        
        # If not a monitored feature, pass through
        if not feature_name:
            return await call_next(request)
        
        # Track metrics for monitored features
        start = time.time()
        
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start) * 1000)
            
            # Log with specified format
            logger.info(
                f"[{feature_name}] endpoint={path} status={response.status_code} duration={duration_ms}ms"
            )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.error(
                f"[{feature_name}] endpoint={path} status=500 duration={duration_ms}ms error={str(e)}"
            )
            raise


# Add middleware and routes
app.add_middleware(TimingMiddleware)
app.add_middleware(FeatureMonitoringMiddleware)  # Monitor new features
app.include_router(ai_routes.router, prefix="/v1/chat", tags=["AI"])
app.include_router(income_ladder.router, prefix="/v1", tags=["Income Ladder"])
app.include_router(tax_optimization.router, prefix="/v1", tags=["Tax Optimization"])
app.include_router(alerts.router, prefix="/v1", tags=["Alerts"])
app.include_router(insights.router, prefix="/v1", tags=["Insights"])
app.include_router(azure_vm.router, prefix="/v1", tags=["Azure VM"])
app.include_router(feedback.router, prefix="/v1", tags=["Feedback & Learning"])
app.include_router(harvey_status.router, prefix="/v1", tags=["Harvey Intelligence"])
app.include_router(dividend_strategies.router, prefix="/v1", tags=["Dividend Strategies"])
app.include_router(training.router, prefix="/v1", tags=["Training Data"])
app.include_router(data_quality.router, prefix="/v1", tags=["Data Quality"])
app.include_router(financial_router, tags=["Financial Models"])
# app.include_router(ml_schedulers.router, prefix="/v1", tags=["ML Schedulers"])  # Temporarily disabled
app.include_router(admin.router, prefix="/v1", tags=["Admin"])

# Include new feature routers
app.include_router(video_routes.router, tags=["Videos"])
app.include_router(dividend_lists_routes.router, tags=["Dividend Lists"])
app.include_router(hashtag_routes.router, tags=["Hashtags"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/v1/pdfco/health")
def pdfco_health_status():
    """
    Get PDF.co service health status and capabilities.
    
    Returns:
        Health status including API availability and credits
    """
    try:
        from app.services.pdfco_service import pdfco_service
        
        health_status = pdfco_service.health_check()
        
        return JSONResponse({
            "success": True,
            "pdfco_status": health_status,
            "capabilities": {
                "pdf_to_text": health_status.get("enabled", False),
                "pdf_to_excel": health_status.get("enabled", False),
                "pdf_to_csv": health_status.get("enabled", False),
                "table_extraction": health_status.get("enabled", False),
                "financial_document_parsing": health_status.get("enabled", False),
                "ocr": health_status.get("enabled", False)
            }
        })
    except Exception as e:
        logger.error(f"Failed to get PDF.co health status: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "pdfco_status": {"status": "error", "enabled": False}
        })


@app.get("/v1/ml/health")
def ml_health_status():
    """
    Get ML API health status and metrics.
    
    Returns:
        Health status including uptime, downtime, and recovery metrics
    """
    try:
        from app.services.ml_health_monitor import get_ml_health_monitor
        from app.services.circuit_breaker import get_ml_circuit_breaker
        
        health_monitor = get_ml_health_monitor()
        circuit_breaker = get_ml_circuit_breaker()
        
        health_status = health_monitor.get_health_status()
        circuit_stats = circuit_breaker.get_stats()
        
        return JSONResponse({
            "success": True,
            "ml_api_health": health_status,
            "circuit_breaker": circuit_stats
        })
    except Exception as e:
        logger.error(f"Failed to get ML health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/ml/circuit-breaker/reset")
async def reset_circuit_breaker(api_key: str = Depends(verify_api_key)):
    """
    Manually reset circuit breaker to CLOSED state.
    
    This is an admin endpoint to force reset the circuit breaker
    when you know the ML API service has recovered.
    
    Returns:
        Success confirmation
    """
    try:
        from app.services.circuit_breaker import get_ml_circuit_breaker
        from datetime import datetime
        
        circuit_breaker = get_ml_circuit_breaker()
        circuit_breaker.reset()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return JSONResponse({
            "success": True,
            "message": "Circuit breaker manually reset to CLOSED state",
            "timestamp": timestamp
        })
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PortfolioAllocation(BaseModel):
    ticker: str
    shares: Optional[float] = None
    target_allocation_pct: Optional[float] = None
    notes: Optional[str] = None


class SavePortfolioRequest(BaseModel):
    name: str = Field(..., description="Portfolio or watchlist name")
    type: str = Field(..., description="Type: 'portfolio' or 'watchlist'")
    allocations: List[Dict] = Field(..., description="List of position allocations")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata (e.g., target_income, years, risk_tolerance)")
    email: Optional[str] = Field(None, description="User email (optional)")


@app.post("/v1/portfolio/save")
async def save_portfolio(request: SavePortfolioRequest, api_key: str = Depends(verify_api_key)):
    """
    Save a portfolio or watchlist with positions.
    
    Args:
        request: Portfolio save request with name, type, allocations, and metadata
        
    Returns:
        Success response with group_id
    """
    try:
        if request.type not in ["portfolio", "watchlist"]:
            raise HTTPException(status_code=400, detail="Type must be 'portfolio' or 'watchlist'")
        
        if not request.allocations:
            raise HTTPException(status_code=400, detail="At least one allocation is required")
        
        user_id = None
        if request.email:
            user_query = text("""
                IF NOT EXISTS (SELECT 1 FROM dbo.user_profiles WHERE email = :email)
                BEGIN
                    INSERT INTO dbo.user_profiles (email, name) VALUES (:email, :email);
                END
                SELECT user_id FROM dbo.user_profiles WHERE email = :email;
            """)
            
            with engine.begin() as conn:
                result = conn.execute(user_query, {"email": request.email})
                row = result.fetchone()
                if row:
                    user_id = row[0]
        
        metadata_json = json.dumps(request.metadata) if request.metadata else None
        
        insert_group_query = text("""
            INSERT INTO dbo.portfolio_groups (user_id, name, type, metadata)
            OUTPUT INSERTED.group_id
            VALUES (:user_id, :name, :type, :metadata);
        """)
        
        with engine.begin() as conn:
            result = conn.execute(insert_group_query, {
                "user_id": user_id,
                "name": request.name,
                "type": request.type,
                "metadata": metadata_json
            })
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to create portfolio group")
            group_id = row[0]
            
            for alloc in request.allocations:
                ticker = alloc.get("ticker")
                if not ticker:
                    continue
                
                shares = alloc.get("shares")
                target_allocation_pct = alloc.get("target_allocation_pct") or alloc.get("allocation_pct")
                notes = alloc.get("notes")
                
                insert_position_query = text("""
                    INSERT INTO dbo.portfolio_positions 
                    (group_id, ticker, shares, target_allocation_pct, notes)
                    VALUES (:group_id, :ticker, :shares, :target_allocation_pct, :notes);
                """)
                
                conn.execute(insert_position_query, {
                    "group_id": group_id,
                    "ticker": ticker,
                    "shares": shares,
                    "target_allocation_pct": target_allocation_pct,
                    "notes": notes
                })
        
        logger.info(f"Successfully saved {request.type} '{request.name}' with group_id={group_id}")
        
        return JSONResponse({
            "success": True,
            "message": f"{request.type.title()} '{request.name}' saved successfully",
            "group_id": group_id,
            "positions_count": len(request.allocations)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save {request.type}: {str(e)}")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.on_event("startup")
async def startup_event():
    """
    Initialize application with performance optimizations.
    
    PERFORMANCE OPTIMIZATIONS:
    - Database indexes for 20-30% faster queries
    - Cache prewarming for 70% cache hit rate
    - Circuit breaker for rate limit protection
    """
    logger.info("[startup] Initializing Harvey with performance optimizations...")
    
    # Initialize database indexes
    try:
        from app.database.init_db import initialize_database
        logger.info("[startup] Applying database performance indexes...")
        initialize_database()
    except Exception as e:
        logger.warning(f"[startup] Database index initialization failed (non-critical): {e}")
    
    # Start background scheduler
    logger.info("[startup] Starting background scheduler...")
    scheduler.start()
    
    # Start cache prewarming (non-blocking background thread)
    try:
        from app.services.cache_prewarmer import start_cache_prewarming
        logger.info("[startup] Starting intelligent cache prewarming...")
        start_cache_prewarming()
        logger.info("[startup] ✓ Cache prewarmer started in background")
    except Exception as e:
        logger.warning(f"[startup] Cache prewarming initialization failed (non-critical): {e}")
    
    # Start ML API health monitor (auto-recovery system)
    try:
        from app.services.ml_health_monitor import get_ml_health_monitor
        logger.info("[startup] Starting ML API health monitor (auto-recovery system)...")
        health_monitor = get_ml_health_monitor()
        health_monitor.start()
        logger.info("[startup] ✓ ML health monitor started - auto-recovery enabled")
    except Exception as e:
        logger.warning(f"[startup] ML health monitor initialization failed (non-critical): {e}")
    
    logger.info("[startup] ✅ Harvey initialized with performance optimizations enabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services on app shutdown."""
    logger.info("[shutdown] Stopping background services...")
    
    # Stop scheduler
    scheduler.stop()
    
    # Stop cache prewarming
    try:
        from app.services.cache_prewarmer import stop_cache_prewarming
        stop_cache_prewarming()
    except Exception as e:
        logger.warning(f"[shutdown] Cache prewarmer stop failed: {e}")
    
    # Stop ML health monitor
    try:
        from app.services.ml_health_monitor import get_ml_health_monitor
        health_monitor = get_ml_health_monitor()
        health_monitor.stop()
    except Exception as e:
        logger.warning(f"[shutdown] ML health monitor stop failed: {e}")
    
    logger.info("[shutdown] ✅ All background services stopped")
