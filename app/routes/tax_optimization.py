"""
Tax Optimization API Routes

Endpoints for tax-efficient dividend investing strategies.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.core.auth import verify_api_key
from app.services import tax_optimization_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tax_optimization_routes")

router = APIRouter()


class AnalyzePortfolioRequest(BaseModel):
    session_id: str = Field(..., description="User session ID")
    portfolio_tickers: Optional[List[str]] = Field(default=None, description="Optional list of tickers to analyze (if None, uses user_portfolios)")
    user_tax_bracket: str = Field(default='medium', description="Tax bracket: low, medium, or high")


class TaxLossHarvestRequest(BaseModel):
    session_id: str = Field(..., description="User session ID")
    min_loss_threshold: float = Field(default=1000, ge=0, description="Minimum loss amount to consider")
    user_tax_bracket: str = Field(default='medium', description="Tax bracket: low, medium, or high")


class TaxScenarioRequest(BaseModel):
    session_id: str = Field(..., description="User session ID")
    scenario_type: str = Field(..., description="Scenario type: current, optimized, or harvest")
    user_tax_bracket: str = Field(default='medium', description="Tax bracket: low, medium, or high")
    harvest_losses: bool = Field(default=False, description="Include tax-loss harvesting in scenario")


@router.post("/tax/analyze-portfolio")
async def analyze_portfolio_taxes(
    request: AnalyzePortfolioRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze portfolio for qualified vs ordinary dividends.
    
    This endpoint identifies which dividends are qualified (lower tax rate) vs ordinary
    and calculates potential tax savings.
    
    Args:
        request: Analysis request with session_id and optional tickers
        
    Returns:
        Analysis with qualified percentage, tax savings, and breakdown by ticker
    """
    try:
        logger.info(
            f"Analyzing portfolio taxes: session={request.session_id}, "
            f"tax_bracket={request.user_tax_bracket}"
        )
        
        result = tax_optimization_service.analyze_qualified_dividends(
            session_id=request.session_id,
            portfolio_tickers=request.portfolio_tickers,
            user_tax_bracket=request.user_tax_bracket
        )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=404 if 'not found' in result.get('error', '').lower() else 500,
                detail=result.get('error', 'Failed to analyze portfolio')
            )
        
        markdown = tax_optimization_service.format_tax_report_markdown(
            qualified_analysis=result,
            harvest_analysis=None,
            scenario=None
        )
        
        result['markdown'] = markdown
        
        logger.info(
            f"Portfolio tax analysis complete: {result.get('qualified_percentage', 0):.1f}% qualified, "
            f"${result.get('tax_savings_estimate', 0):.2f} potential savings"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing portfolio taxes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze portfolio: {str(e)}"
        )


@router.post("/tax/harvest-opportunities")
async def find_harvest_opportunities(
    request: TaxLossHarvestRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Find tax-loss harvesting opportunities in user's portfolio.
    
    This endpoint identifies positions with unrealized losses that can be sold
    to reduce tax burden, along with replacement ticker suggestions.
    
    Args:
        request: Harvest request with session_id and minimum loss threshold
        
    Returns:
        List of opportunities with replacement suggestions and estimated tax savings
    """
    try:
        logger.info(
            f"Finding tax-loss harvest opportunities: session={request.session_id}, "
            f"min_loss=${request.min_loss_threshold}"
        )
        
        result = tax_optimization_service.find_tax_loss_harvest_opportunities(
            session_id=request.session_id,
            min_loss_threshold=request.min_loss_threshold,
            user_tax_bracket=request.user_tax_bracket
        )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to find harvest opportunities')
            )
        
        markdown = tax_optimization_service.format_tax_report_markdown(
            qualified_analysis={'total_dividend_income': 0, 'qualified_dividends': 0, 'ordinary_dividends': 0, 'qualified_percentage': 0, 'recommendations': []},
            harvest_analysis=result,
            scenario=None
        )
        
        result['markdown'] = markdown
        
        logger.info(
            f"Found {len(result.get('opportunities', []))} tax-loss harvest opportunities "
            f"totaling ${result.get('total_harvestable_losses', 0):,.2f}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding harvest opportunities: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find harvest opportunities: {str(e)}"
        )


@router.post("/tax/scenario")
async def calculate_scenario(
    request: TaxScenarioRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Calculate tax implications of different scenarios.
    
    This endpoint compares different tax scenarios:
    - 'current': Current portfolio tax situation
    - 'optimized': If all dividends were qualified
    - 'harvest': Including tax-loss harvesting
    
    Args:
        request: Scenario request with session_id and scenario type
        
    Returns:
        Tax scenario analysis with estimated taxes and savings
    """
    try:
        if request.scenario_type not in ['current', 'optimized', 'harvest']:
            raise HTTPException(
                status_code=400,
                detail="scenario_type must be 'current', 'optimized', or 'harvest'"
            )
        
        logger.info(
            f"Calculating tax scenario: session={request.session_id}, "
            f"type={request.scenario_type}"
        )
        
        result = tax_optimization_service.calculate_tax_scenario(
            session_id=request.session_id,
            scenario_type=request.scenario_type,
            user_tax_bracket=request.user_tax_bracket,
            harvest_losses=request.harvest_losses
        )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=404 if 'not found' in result.get('error', '').lower() else 500,
                detail=result.get('error', 'Failed to calculate scenario')
            )
        
        qualified_analysis = tax_optimization_service.analyze_qualified_dividends(
            session_id=request.session_id,
            user_tax_bracket=request.user_tax_bracket
        )
        
        harvest_analysis = None
        if request.scenario_type == 'harvest' or request.harvest_losses:
            harvest_analysis = tax_optimization_service.find_tax_loss_harvest_opportunities(
                session_id=request.session_id,
                min_loss_threshold=500,
                user_tax_bracket=request.user_tax_bracket
            )
        
        markdown = tax_optimization_service.format_tax_report_markdown(
            qualified_analysis=qualified_analysis,
            harvest_analysis=harvest_analysis,
            scenario=result
        )
        
        result['markdown'] = markdown
        
        logger.info(
            f"Tax scenario '{request.scenario_type}' calculated: "
            f"${result.get('total_tax_owed', 0):.2f} tax on "
            f"${result.get('annual_dividend_income', 0):.2f} income"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating tax scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate scenario: {str(e)}"
        )


@router.get("/tax/recommendations/{session_id}")
async def get_recommendations(
    session_id: str,
    user_tax_bracket: str = Query(default='medium', description="Tax bracket: low, medium, or high"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get AI-powered tax optimization recommendations.
    
    This endpoint uses GPT-4o to analyze the portfolio and generate
    personalized tax optimization strategies.
    
    Args:
        session_id: User session ID
        user_tax_bracket: Tax bracket (low, medium, high)
        
    Returns:
        AI-generated recommendations in markdown format
    """
    try:
        logger.info(f"Generating AI tax recommendations for session: {session_id}")
        
        result = tax_optimization_service.get_tax_efficient_recommendations(
            session_id=session_id,
            user_tax_bracket=user_tax_bracket
        )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to generate recommendations')
            )
        
        logger.info(f"AI tax recommendations generated for session {session_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/tax/scenarios/{session_id}")
async def list_tax_scenarios(
    session_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    """
    List all saved tax scenarios for a session.
    
    Args:
        session_id: User session ID
        limit: Maximum number of scenarios to return (1-100)
        
    Returns:
        List of saved tax scenarios
    """
    try:
        from sqlalchemy import text
        from app.core.database import engine
        
        logger.info(f"Listing tax scenarios for session: {session_id}")
        
        query = text("""
            SELECT TOP (:limit)
                scenario_id,
                scenario_type,
                potential_savings,
                tax_year,
                created_at
            FROM dbo.tax_scenarios
            WHERE session_id = :session_id
            ORDER BY created_at DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {
                'session_id': session_id,
                'limit': limit
            })
            rows = result.fetchall()
        
        scenarios = []
        for row in rows:
            scenarios.append({
                'scenario_id': row[0],
                'scenario_type': row[1],
                'potential_savings': float(row[2]) if row[2] else 0.0,
                'tax_year': int(row[3]) if row[3] else datetime.now().year,
                'created_at': row[4].isoformat() if row[4] else None
            })
        
        logger.info(f"Found {len(scenarios)} tax scenarios for session {session_id}")
        
        return {
            'success': True,
            'session_id': session_id,
            'count': len(scenarios),
            'scenarios': scenarios
        }
        
    except Exception as e:
        logger.error(f"Error listing tax scenarios: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tax scenarios: {str(e)}"
        )
