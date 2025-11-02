"""
Dividend Strategy Analysis API Endpoints
Provides advanced dividend investment strategy recommendations.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from app.core.auth import verify_api_key
from app.services.dividend_strategy_analyzer import dividend_strategy

logger = logging.getLogger("dividend_strategies_api")

router = APIRouter()


class StrategyAnalysisRequest(BaseModel):
    """Request model for dividend strategy analysis"""
    symbol: str = Field(..., description="Stock ticker symbol")
    current_price: float = Field(..., description="Current stock price")
    dividend_yield: float = Field(..., description="Annual dividend yield percentage")
    ex_date: Optional[str] = Field(None, description="Ex-dividend date (YYYY-MM-DD)")
    declaration_date: Optional[str] = Field(None, description="Declaration date (YYYY-MM-DD)")
    volatility: Optional[float] = Field(None, description="Stock volatility percentage")
    margin_rate: float = Field(7.0, description="Margin interest rate")
    tax_rate: float = Field(0.15, description="Tax rate on dividends (0.15 for qualified, 0.37 for ordinary)")
    capital_available: float = Field(10000, description="Available capital for investment")
    risk_tolerance: str = Field("MEDIUM", description="Risk tolerance: LOW, MEDIUM, HIGH")


class CalendarStrategyRequest(BaseModel):
    """Request model for calendar-based strategy analysis"""
    symbol: str = Field(..., description="Stock ticker symbol")
    declaration_date: str = Field(..., description="Declaration date (YYYY-MM-DD)")
    ex_date: str = Field(..., description="Ex-dividend date (YYYY-MM-DD)")
    record_date: str = Field(..., description="Record date (YYYY-MM-DD)")
    payment_date: str = Field(..., description="Payment date (YYYY-MM-DD)")
    current_date: Optional[str] = Field(None, description="Current date for analysis (YYYY-MM-DD)")


@router.post("/dividend-strategies/analyze")
async def analyze_dividend_strategies(
    request: StrategyAnalysisRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze and recommend optimal dividend investment strategies for a stock.
    
    Strategies analyzed:
    - Margin Buying: Use leverage to amplify dividend income
    - DRIP: Automatic dividend reinvestment for compound growth
    - Dividend Capture: Buy before ex-date, sell after for quick income
    - Ex-Date Dip Buying: Buy on typical price drop on ex-dividend date
    - Declaration Play: Buy on declaration, sell after ex-date
    - Covered Call: Combine dividends with option premium income
    - Put Writing: Generate income while waiting to acquire shares
    
    Returns:
        Comprehensive strategy analysis with calculations and recommendations
    """
    try:
        logger.info(f"Analyzing dividend strategies for {request.symbol}")
        
        # Parse dates if provided
        ex_date = datetime.strptime(request.ex_date, "%Y-%m-%d") if request.ex_date else None
        declaration_date = datetime.strptime(request.declaration_date, "%Y-%m-%d") if request.declaration_date else None
        
        # Analyze strategies
        analysis = dividend_strategy.analyze_strategy(
            symbol=request.symbol,
            current_price=request.current_price,
            dividend_yield=request.dividend_yield,
            ex_date=ex_date,
            declaration_date=declaration_date,
            volatility=request.volatility,
            margin_rate=request.margin_rate,
            tax_rate=request.tax_rate,
            capital_available=request.capital_available,
            risk_tolerance=request.risk_tolerance
        )
        
        return JSONResponse({
            "success": True,
            "analysis": analysis
        })
        
    except Exception as e:
        logger.error(f"Failed to analyze dividend strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dividend-strategies/calendar")
async def get_calendar_strategy(
    request: CalendarStrategyRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Get date-specific dividend strategy recommendations based on dividend calendar.
    
    Provides optimal actions for each phase of the dividend cycle:
    - Pre-declaration: Accumulation strategies
    - Post-declaration: Declaration play timing
    - Pre ex-date: Dividend capture setup
    - Ex-date: Dip buying opportunities
    - Post ex-date: Recovery strategies
    
    Returns:
        Timeline-based strategy recommendations
    """
    try:
        logger.info(f"Getting calendar strategy for {request.symbol}")
        
        # Parse dates
        declaration = datetime.strptime(request.declaration_date, "%Y-%m-%d")
        ex = datetime.strptime(request.ex_date, "%Y-%m-%d")
        record = datetime.strptime(request.record_date, "%Y-%m-%d")
        payment = datetime.strptime(request.payment_date, "%Y-%m-%d")
        current = datetime.strptime(request.current_date, "%Y-%m-%d") if request.current_date else datetime.now()
        
        # Get calendar-based strategy
        calendar_strategy = dividend_strategy.get_calendar_strategy(
            symbol=request.symbol,
            declaration_date=declaration,
            ex_date=ex,
            record_date=record,
            payment_date=payment,
            current_date=current
        )
        
        return JSONResponse({
            "success": True,
            "calendar_strategy": calendar_strategy
        })
        
    except Exception as e:
        logger.error(f"Failed to get calendar strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dividend-strategies/list")
async def list_dividend_strategies(api_key: str = Depends(verify_api_key)):
    """
    List all available dividend investment strategies with descriptions.
    
    Returns:
        List of strategies with profiles including pros, cons, and best use cases
    """
    try:
        strategies_list = []
        
        for strategy_type, profile in dividend_strategy.strategies.items():
            strategies_list.append({
                "id": strategy_type.value,
                "name": profile["name"],
                "description": profile["description"],
                "risk_level": profile["risk_level"],
                "capital_required": profile["capital_required"],
                "pros": profile["pros"],
                "cons": profile["cons"],
                "best_for": profile["best_for"]
            })
        
        return JSONResponse({
            "success": True,
            "strategies": strategies_list,
            "total": len(strategies_list)
        })
        
    except Exception as e:
        logger.error(f"Failed to list strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dividend-strategies/compare")
async def compare_strategies(
    symbol: str,
    strategies: List[str],
    api_key: str = Depends(verify_api_key)
):
    """
    Compare multiple dividend strategies side-by-side for a given stock.
    
    Args:
        symbol: Stock ticker symbol
        strategies: List of strategy IDs to compare
    
    Returns:
        Side-by-side comparison of selected strategies
    """
    try:
        logger.info(f"Comparing strategies {strategies} for {symbol}")
        
        # This would fetch real data in production
        # For now, return a comparison structure
        comparison = {
            "symbol": symbol,
            "strategies_compared": strategies,
            "comparison": [
                {
                    "strategy": strategy,
                    "expected_return": "Varies",
                    "risk_level": "Varies",
                    "time_commitment": "Varies",
                    "capital_efficiency": "Varies"
                }
                for strategy in strategies
            ]
        }
        
        return JSONResponse({
            "success": True,
            "comparison": comparison
        })
        
    except Exception as e:
        logger.error(f"Failed to compare strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))