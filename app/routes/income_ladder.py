"""
Income Ladder API Routes

Endpoints for building and managing monthly income ladders.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.core.auth import verify_api_key
from app.services import income_ladder_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("income_ladder_routes")

router = APIRouter()


class BuildIncomeLadderRequest(BaseModel):
    session_id: str = Field(..., description="User session ID")
    target_monthly_income: float = Field(..., gt=0, description="Target monthly income amount")
    risk_tolerance: str = Field(default='moderate', description="Risk tolerance: conservative, moderate, or aggressive")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="Optional preferences (sectors_to_avoid, min_yield, etc)")


class IncomeLadderResponse(BaseModel):
    success: bool
    ladder_id: Optional[str] = None
    target_monthly_income: float
    total_capital_needed: float
    monthly_allocations: Dict
    diversification: Dict
    annual_income: float
    effective_yield: float
    risk_tolerance: Optional[str] = None
    created_at: Optional[str] = None
    markdown: Optional[str] = None
    error: Optional[str] = None


@router.post("/income-ladder/build", response_model=IncomeLadderResponse)
async def build_income_ladder_endpoint(
    request: BuildIncomeLadderRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Build a monthly income ladder portfolio.
    
    This endpoint creates a diversified portfolio of dividend-paying stocks
    that generate income every month of the year.
    
    Args:
        request: Build request with target income and preferences
        
    Returns:
        Income ladder plan with monthly allocations and diversification
    """
    try:
        logger.info(
            f"Building income ladder: session={request.session_id}, "
            f"target=${request.target_monthly_income}/month, risk={request.risk_tolerance}"
        )
        
        ladder = income_ladder_service.build_income_ladder(
            session_id=request.session_id,
            target_monthly_income=request.target_monthly_income,
            risk_tolerance=request.risk_tolerance,
            preferences=request.preferences or {}
        )
        
        if not ladder.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=ladder.get('error', 'Failed to build income ladder')
            )
        
        markdown = income_ladder_service.format_ladder_markdown(ladder)
        ladder['markdown'] = markdown
        
        logger.info(
            f"Successfully built income ladder {ladder['ladder_id']}: "
            f"${ladder['annual_income']:.2f}/year from ${ladder['total_capital_needed']:.2f} capital"
        )
        
        return IncomeLadderResponse(**ladder)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building income ladder: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build income ladder: {str(e)}"
        )


@router.get("/income-ladder/{ladder_id}")
async def get_income_ladder(
    ladder_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve a saved income ladder by ID.
    
    Args:
        ladder_id: The ladder ID to retrieve
        
    Returns:
        Income ladder details with monthly allocations
    """
    try:
        logger.info(f"Retrieving income ladder: {ladder_id}")
        
        ladder = income_ladder_service.get_income_ladder(ladder_id)
        
        if not ladder:
            raise HTTPException(
                status_code=404,
                detail=f"Income ladder {ladder_id} not found"
            )
        
        annual_income = sum(
            sum(pos.get('monthly_dividend', 0) for pos in positions)
            for positions in ladder.get('monthly_allocations', {}).values()
        ) * 12
        
        effective_yield = (
            (annual_income / ladder['total_capital_needed'] * 100)
            if ladder.get('total_capital_needed', 0) > 0
            else 0
        )
        
        ladder['annual_income'] = round(annual_income, 2)
        ladder['effective_yield'] = round(effective_yield, 2)
        ladder['success'] = True
        
        markdown = income_ladder_service.format_ladder_markdown(ladder)
        ladder['markdown'] = markdown
        
        logger.info(f"Successfully retrieved income ladder {ladder_id}")
        
        return ladder
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving income ladder: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve income ladder: {str(e)}"
        )


@router.get("/income-ladder/session/{session_id}")
async def list_user_ladders(
    session_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    """
    List all income ladders for a session.
    
    Args:
        session_id: User session ID
        limit: Maximum number of ladders to return (1-100)
        
    Returns:
        List of income ladder summaries
    """
    try:
        logger.info(f"Listing income ladders for session: {session_id}")
        
        ladders = income_ladder_service.get_user_income_ladders(
            session_id=session_id,
            limit=limit
        )
        
        logger.info(f"Found {len(ladders)} income ladders for session {session_id}")
        
        return {
            'success': True,
            'session_id': session_id,
            'count': len(ladders),
            'ladders': ladders
        }
        
    except Exception as e:
        logger.error(f"Error listing income ladders: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list income ladders: {str(e)}"
        )
