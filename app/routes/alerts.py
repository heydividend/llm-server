"""
Natural Language Alerts API Routes

Endpoints for creating, managing, and monitoring natural language alerts.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.auth import verify_api_key
from app.services import alert_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alerts_routes")

router = APIRouter()


class CreateAlertRequest(BaseModel):
    session_id: str = Field(..., description="User session ID")
    natural_language: str = Field(..., description="Natural language alert request")


class AlertResponse(BaseModel):
    success: bool
    alert_id: Optional[str] = None
    rule_name: Optional[str] = None
    condition_type: Optional[str] = None
    ticker: Optional[str] = None
    trigger_condition: Optional[dict] = None
    is_active: Optional[bool] = None
    error: Optional[str] = None
    markdown: Optional[str] = None


@router.post("/alerts/create", response_model=AlertResponse)
async def create_alert(
    request: CreateAlertRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Create an alert from natural language request.
    
    Examples:
    - "Tell me when AAPL goes above $200"
    - "Alert me if any of my stocks cut their dividend"
    - "Notify me when VYM yield exceeds 4%"
    
    The system uses GPT-4o to parse the natural language into a structured alert rule.
    
    Args:
        request: Alert creation request with session ID and natural language
        
    Returns:
        Alert details with success status and formatted markdown response
    """
    try:
        logger.info(
            f"Creating alert for session {request.session_id}: "
            f"'{request.natural_language}'"
        )
        
        result = alert_service.create_alert_from_natural_language(
            session_id=request.session_id,
            natural_language=request.natural_language
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to create alert")
            )
        
        ticker_info = f" for {result['ticker']}" if result.get("ticker") else ""
        
        markdown = f"""## ✅ Alert Created

**Alert:** {result['rule_name']}
**Type:** {result['condition_type'].replace('_', ' ').title()}{ticker_info}
**Status:** Active
**Will notify:** When condition is met

You can manage your alerts at any time through the alerts API."""
        
        result["markdown"] = markdown
        
        logger.info(
            f"Successfully created alert {result['alert_id']}: {result['rule_name']}"
        )
        
        return AlertResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alert: {str(e)}"
        )


@router.get("/alerts/session/{session_id}")
async def list_alerts(
    session_id: str,
    active_only: bool = Query(default=True, description="Only return active alerts"),
    api_key: str = Depends(verify_api_key)
):
    """
    List all alerts for a session.
    
    Args:
        session_id: User session ID
        active_only: If True, only return active alerts
        
    Returns:
        List of alert rules with metadata
    """
    try:
        logger.info(f"Listing alerts for session {session_id} (active_only={active_only})")
        
        alerts = alert_service.get_user_alerts(
            session_id=session_id,
            active_only=active_only
        )
        
        logger.info(f"Found {len(alerts)} alerts for session {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Error listing alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list alerts: {str(e)}"
        )


@router.get("/alerts/events/{session_id}")
async def list_alert_events(
    session_id: str,
    unread_only: bool = Query(default=True, description="Only return unread events"),
    limit: int = Query(default=50, ge=1, le=200),
    api_key: str = Depends(verify_api_key)
):
    """
    List triggered alerts (alert events) for a session.
    
    Args:
        session_id: User session ID
        unread_only: If True, only return unread events
        limit: Maximum number of events to return (1-200)
        
    Returns:
        List of triggered alert events (notifications)
    """
    try:
        logger.info(
            f"Listing alert events for session {session_id} "
            f"(unread_only={unread_only}, limit={limit})"
        )
        
        events = alert_service.get_alert_events(
            session_id=session_id,
            unread_only=unread_only,
            limit=limit
        )
        
        logger.info(f"Found {len(events)} alert events for session {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "count": len(events),
            "events": events
        }
        
    except Exception as e:
        logger.error(f"Error listing alert events: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list alert events: {str(e)}"
        )


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete an alert rule.
    
    This will also delete all associated alert events (cascading delete).
    
    Args:
        alert_id: Alert ID to delete
        
    Returns:
        Success confirmation
    """
    try:
        logger.info(f"Deleting alert {alert_id}")
        
        success = alert_service.delete_alert(alert_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Alert {alert_id} not found or could not be deleted"
            )
        
        logger.info(f"Successfully deleted alert {alert_id}")
        
        return {
            "success": True,
            "message": f"Alert {alert_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete alert: {str(e)}"
        )


@router.put("/alerts/events/{event_id}/read")
async def mark_alert_event_read(
    event_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Mark an alert event as read.
    
    Args:
        event_id: Alert event ID to mark as read
        
    Returns:
        Success confirmation
    """
    try:
        logger.info(f"Marking alert event {event_id} as read")
        
        success = alert_service.mark_alert_event_read(event_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Alert event {event_id} not found or could not be updated"
            )
        
        logger.info(f"Successfully marked alert event {event_id} as read")
        
        return {
            "success": True,
            "message": f"Alert event {event_id} marked as read"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alert event as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark alert event as read: {str(e)}"
        )


@router.post("/alerts/check")
async def check_alerts(
    alert_id: Optional[str] = Query(default=None, description="Check specific alert, or all if not provided"),
    api_key: str = Depends(verify_api_key)
):
    """
    Manually trigger alert condition checking.
    
    This is useful for testing or immediate checking without waiting for the scheduler.
    
    Args:
        alert_id: Optional specific alert to check, or None for all active alerts
        
    Returns:
        List of triggered alerts
    """
    try:
        if alert_id:
            logger.info(f"Manually checking alert {alert_id}")
        else:
            logger.info("Manually checking all active alerts")
        
        triggered = alert_service.check_alert_conditions(alert_id)
        
        logger.info(f"Alert check complete: {len(triggered)} alerts triggered")
        
        return {
            "success": True,
            "checked": 1 if alert_id else "all",
            "triggered_count": len(triggered),
            "triggered_alerts": triggered
        }
        
    except Exception as e:
        logger.error(f"Error checking alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check alerts: {str(e)}"
        )
