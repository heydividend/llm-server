"""
Proactive Insights API Routes

Endpoints for retrieving and managing daily digests and portfolio insights.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.auth import verify_api_key
from app.services import insights_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("insights_routes")

router = APIRouter()


class GenerateDigestRequest(BaseModel):
    session_id: str = Field(..., description="User session ID")


@router.get("/insights/{session_id}")
async def get_insights(
    session_id: str,
    unread_only: bool = Query(default=True, description="Only return unread insights"),
    limit: int = Query(default=10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    """
    Get insights and notifications for a session.
    
    Insights include:
    - Daily portfolio digests
    - Significant price change alerts
    - Dividend announcements
    - Ex-dividend date reminders
    
    Args:
        session_id: User session ID
        unread_only: If True, only return unread insights
        limit: Maximum number of insights to return (1-100)
        
    Returns:
        List of insights ordered by priority and date
    """
    try:
        logger.info(
            f"Getting insights for session {session_id} "
            f"(unread_only={unread_only}, limit={limit})"
        )
        
        if unread_only:
            insights = insights_service.get_unread_insights(
                session_id=session_id,
                limit=limit
            )
        else:
            insights = insights_service.get_all_insights(
                session_id=session_id,
                limit=limit
            )
        
        logger.info(f"Retrieved {len(insights)} insights for session {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "count": len(insights),
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get insights: {str(e)}"
        )


@router.post("/insights/generate-digest")
async def generate_digest(
    request: GenerateDigestRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually trigger daily digest generation for a session.
    
    This bypasses the normal daily schedule (8 AM) and generates a digest immediately.
    Useful for testing or on-demand digest requests.
    
    Args:
        request: Digest generation request with session ID
        
    Returns:
        Generated digest with content and metadata
    """
    try:
        logger.info(f"Generating digest for session {request.session_id}")
        
        result = insights_service.generate_daily_digest(request.session_id)
        
        if not result.get("success", False):
            error_msg = result.get("message") or result.get("error", "Unknown error")
            
            if "No portfolio holdings" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail="No portfolio holdings found for this session"
                )
            
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        logger.info(
            f"Successfully generated digest {result['insight_id']} "
            f"for session {request.session_id}"
        )
        
        return {
            "success": True,
            "insight_id": result["insight_id"],
            "title": result["title"],
            "content": result["content"],
            "priority": result["priority"],
            "metadata": result.get("metadata", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating digest: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate digest: {str(e)}"
        )


@router.put("/insights/{insight_id}/read")
async def mark_insight_read(
    insight_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Mark an insight as read.
    
    Args:
        insight_id: Insight ID to mark as read
        
    Returns:
        Success confirmation
    """
    try:
        logger.info(f"Marking insight {insight_id} as read")
        
        success = insights_service.mark_insight_read(insight_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Insight {insight_id} not found or could not be updated"
            )
        
        logger.info(f"Successfully marked insight {insight_id} as read")
        
        return {
            "success": True,
            "message": f"Insight {insight_id} marked as read"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking insight as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark insight as read: {str(e)}"
        )


@router.post("/insights/portfolio-alert")
async def create_portfolio_alert(
    session_id: str = Query(..., description="User session ID"),
    alert_type: str = Query(..., description="Alert type: significant_change, dividend_announcement, ex_date_reminder"),
    ticker: str = Query(..., description="Stock ticker symbol"),
    api_key: str = Depends(verify_api_key)
):
    """
    Create a portfolio-specific alert.
    
    This is typically called by the system when detecting significant events,
    but can also be triggered manually for testing.
    
    Args:
        session_id: User session ID
        alert_type: Type of alert to generate
        ticker: Stock ticker symbol
        
    Returns:
        Generated alert insight
    """
    try:
        logger.info(
            f"Creating portfolio alert: {alert_type} for {ticker} "
            f"(session {session_id})"
        )
        
        if alert_type not in ["significant_change", "dividend_announcement", "ex_date_reminder"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid alert_type. Must be: significant_change, dividend_announcement, or ex_date_reminder"
            )
        
        details = {
            "ticker": ticker,
            "current_price": 100.0,
            "change_pct": 5.5,
            "price_change": 5.5
        }
        
        result = insights_service.generate_portfolio_alert(
            session_id=session_id,
            alert_type=alert_type,
            ticker=ticker,
            details=details
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create portfolio alert")
            )
        
        logger.info(
            f"Successfully created portfolio alert {result['insight_id']}"
        )
        
        return {
            "success": True,
            "insight_id": result["insight_id"],
            "title": result["title"],
            "content": result["content"],
            "priority": result["priority"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portfolio alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create portfolio alert: {str(e)}"
        )
