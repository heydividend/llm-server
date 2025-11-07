"""
ML Schedulers API Routes
Provides endpoints for ML scheduler services running on Azure VM
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from app.core.auth import get_api_key
from app.services.ml_schedulers_service import MLSchedulersService
from app.core.self_healing import self_healing_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ml-schedulers", tags=["ml-schedulers"])

# Initialize service
ml_schedulers_service = MLSchedulersService()


class PayoutRatingRequest(BaseModel):
    """Request for payout rating generation"""
    symbols: List[str]
    force_refresh: bool = False


class DividendCalendarRequest(BaseModel):
    """Request for dividend calendar predictions"""
    symbols: List[str]
    months_ahead: int = 6


class SchedulerStatusResponse(BaseModel):
    """Response for scheduler status"""
    service_name: str
    status: str  # running, stopped, error
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    health_status: str
    recent_errors: List[str]


@router.get("/health")
async def get_ml_schedulers_health(api_key: str = Depends(get_api_key)):
    """
    Get health status of all ML schedulers
    """
    try:
        health = await ml_schedulers_service.get_health_status()
        return {
            "status": "healthy" if health["all_healthy"] else "degraded",
            "schedulers": health["schedulers"],
            "last_check": health["last_check"],
            "message": health["message"]
        }
    except Exception as e:
        logger.error(f"Error checking ML schedulers health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payout-rating")
async def get_payout_rating(
    request: PayoutRatingRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """
    Get dividend payout ratings (A+/A/B/C) for symbols
    Uses daily ML predictions from 1 AM scheduler
    """
    try:
        # Check circuit breaker
        if not self_healing_manager.check_circuit("ml_payout_rating"):
            raise HTTPException(
                status_code=503, 
                detail="Payout rating service temporarily unavailable"
            )
        
        ratings = await ml_schedulers_service.get_payout_ratings(
            request.symbols,
            force_refresh=request.force_refresh
        )
        
        # Record success
        self_healing_manager.record_success("ml_payout_rating")
        
        return {
            "ratings": ratings,
            "source": "ML Payout Rating Scheduler",
            "last_update": ratings.get("last_update"),
            "cached": not request.force_refresh
        }
        
    except Exception as e:
        logger.error(f"Error getting payout ratings: {e}")
        self_healing_manager.record_failure("ml_payout_rating", str(e))
        
        # Schedule self-healing
        background_tasks.add_task(
            self_healing_manager.attempt_recovery,
            "ml_payout_rating"
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dividend-calendar")
async def get_dividend_calendar(
    request: DividendCalendarRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """
    Get predicted dividend payment dates
    Uses weekly ML predictions from Sunday 2 AM scheduler
    """
    try:
        # Check circuit breaker
        if not self_healing_manager.check_circuit("ml_dividend_calendar"):
            raise HTTPException(
                status_code=503,
                detail="Dividend calendar service temporarily unavailable"
            )
        
        predictions = await ml_schedulers_service.get_dividend_calendar(
            request.symbols,
            months_ahead=request.months_ahead
        )
        
        # Record success
        self_healing_manager.record_success("ml_dividend_calendar")
        
        return {
            "predictions": predictions,
            "source": "ML Dividend Calendar Scheduler",
            "months_ahead": request.months_ahead,
            "last_update": predictions.get("last_update")
        }
        
    except Exception as e:
        logger.error(f"Error getting dividend calendar: {e}")
        self_healing_manager.record_failure("ml_dividend_calendar", str(e))
        
        # Schedule self-healing
        background_tasks.add_task(
            self_healing_manager.attempt_recovery,
            "ml_dividend_calendar"
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/status")
async def get_training_status(api_key: str = Depends(get_api_key)):
    """
    Get status of ML model training
    Training runs weekly on Sunday 3 AM
    """
    try:
        status = await ml_schedulers_service.get_training_status()
        return {
            "status": status["status"],
            "last_training": status["last_training"],
            "next_training": status["next_training"],
            "models_trained": status["models_trained"],
            "training_metrics": status["metrics"],
            "message": status["message"]
        }
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/trigger")
async def trigger_training(
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """
    Manually trigger ML model training
    Admin endpoint to force training outside schedule
    """
    try:
        # Add training to background tasks
        background_tasks.add_task(
            ml_schedulers_service.trigger_training
        )
        
        return {
            "message": "Training triggered successfully",
            "status": "started",
            "note": "Training runs in background, check status endpoint for progress"
        }
    except Exception as e:
        logger.error(f"Error triggering training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/status")
async def get_admin_status(api_key: str = Depends(get_api_key)):
    """
    Admin endpoint for comprehensive ML scheduler status
    """
    try:
        status = await ml_schedulers_service.get_comprehensive_status()
        
        return {
            "service": "heydividend-ml-schedulers",
            "vm_ip": "20.81.210.213",
            "schedulers": {
                "payout_rating": {
                    "schedule": "Daily 1:00 AM",
                    "status": status["payout_rating"]["status"],
                    "last_run": status["payout_rating"]["last_run"],
                    "next_run": status["payout_rating"]["next_run"],
                    "recent_errors": status["payout_rating"]["errors"]
                },
                "dividend_calendar": {
                    "schedule": "Sunday 2:00 AM",
                    "status": status["dividend_calendar"]["status"],
                    "last_run": status["dividend_calendar"]["last_run"],
                    "next_run": status["dividend_calendar"]["next_run"],
                    "recent_errors": status["dividend_calendar"]["errors"]
                },
                "ml_training": {
                    "schedule": "Sunday 3:00 AM",
                    "status": status["ml_training"]["status"],
                    "last_run": status["ml_training"]["last_run"],
                    "next_run": status["ml_training"]["next_run"],
                    "models": status["ml_training"]["models"],
                    "recent_errors": status["ml_training"]["errors"]
                }
            },
            "self_healing": {
                "circuit_breakers": status["circuit_breakers"],
                "recent_recoveries": status["recent_recoveries"],
                "health_score": status["health_score"]
            },
            "system_metrics": {
                "cpu_usage": status["cpu_usage"],
                "memory_usage": status["memory_usage"],
                "disk_usage": status["disk_usage"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting admin status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/restart-scheduler")
async def restart_scheduler(
    scheduler_name: str,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """
    Admin endpoint to restart specific scheduler
    """
    valid_schedulers = ["payout_rating", "dividend_calendar", "ml_training"]
    
    if scheduler_name not in valid_schedulers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scheduler. Must be one of: {valid_schedulers}"
        )
    
    try:
        # Add restart to background tasks
        background_tasks.add_task(
            ml_schedulers_service.restart_scheduler,
            scheduler_name
        )
        
        return {
            "message": f"Restart initiated for {scheduler_name}",
            "status": "restarting",
            "note": "Check status endpoint in 30 seconds"
        }
    except Exception as e:
        logger.error(f"Error restarting scheduler {scheduler_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))