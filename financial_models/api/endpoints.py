"""
Financial Models API Endpoints
FastAPI routes for Portfolio and Watchlist Projection Engine
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging

from financial_models.engines.portfolio_projection import PortfolioProjectionEngine
from financial_models.engines.watchlist_projection import WatchlistProjectionEngine
from financial_models.engines.sustainability_analyzer import DividendSustainabilityAnalyzer
from financial_models.engines.cashflow_sensitivity import CashFlowSensitivityModel
from financial_models.utils.database import FinancialDataExtractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/financial", tags=["financial-models"])

INTERNAL_ML_API_KEY = os.getenv('INTERNAL_ML_API_KEY')

if not INTERNAL_ML_API_KEY:
    raise ValueError(
        "INTERNAL_ML_API_KEY environment variable is required for financial models API. "
        "Please set it in your environment or .env file."
    )

data_extractor = FinancialDataExtractor()
portfolio_engine = PortfolioProjectionEngine(data_extractor)
watchlist_engine = WatchlistProjectionEngine(data_extractor)
sustainability_analyzer = DividendSustainabilityAnalyzer(data_extractor)
cashflow_model = CashFlowSensitivityModel(data_extractor)


async def verify_api_key(x_internal_api_key: str = Header()):
    """Verify internal API key"""
    if x_internal_api_key != INTERNAL_ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_internal_api_key


class PortfolioProjectionRequest(BaseModel):
    user_id: Optional[str] = None
    years: int = 10


class WatchlistAnalysisRequest(BaseModel):
    user_id: Optional[str] = None
    investment_amount: float = 10000


class OptimalAllocationRequest(BaseModel):
    user_id: Optional[str] = None
    target_monthly_income: float = 1000
    total_capital: float = 100000


class SustainabilityAnalysisRequest(BaseModel):
    ticker: Optional[str] = None
    user_id: Optional[str] = None


class CashFlowSensitivityRequest(BaseModel):
    user_id: Optional[str] = None
    custom_scenarios: Optional[List[Dict[str, Any]]] = None


@router.post("/portfolio/projection", dependencies=[Depends(verify_api_key)])
async def analyze_portfolio_projection(request: PortfolioProjectionRequest):
    """
    Analyze portfolio and project 1/3/5/10 year dividend income
    
    Returns comprehensive projections with growth modeling based on historical data
    """
    try:
        result = portfolio_engine.analyze_portfolio(request.user_id)
        return result
    except Exception as e:
        logger.error(f"Error in portfolio projection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist/analyze", dependencies=[Depends(verify_api_key)])
async def analyze_watchlist(request: WatchlistAnalysisRequest):
    """
    Analyze watchlist stocks and project potential income
    
    Shows what-if scenarios with given investment amount
    """
    try:
        result = watchlist_engine.analyze_watchlist(
            request.user_id,
            request.investment_amount
        )
        return result
    except Exception as e:
        logger.error(f"Error in watchlist analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist/optimal-allocation", dependencies=[Depends(verify_api_key)])
async def calculate_optimal_allocation(request: OptimalAllocationRequest):
    """
    Calculate optimal allocation to achieve target monthly income
    
    Returns recommended positions with diversification constraints
    """
    try:
        watchlist = data_extractor.get_watchlist_stocks(request.user_id)
        result = watchlist_engine.calculate_optimal_allocation(
            watchlist,
            request.target_monthly_income,
            request.total_capital
        )
        return result
    except Exception as e:
        logger.error(f"Error in optimal allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sustainability/stock", dependencies=[Depends(verify_api_key)])
async def analyze_stock_sustainability(request: SustainabilityAnalysisRequest):
    """
    Analyze dividend sustainability for a single stock
    
    Provides payout ratio health, cut risk, and overall grade
    """
    try:
        if not request.ticker:
            raise HTTPException(status_code=400, detail="ticker is required")
        
        result = sustainability_analyzer.analyze_stock_sustainability(request.ticker)
        return result
    except Exception as e:
        logger.error(f"Error in sustainability analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sustainability/portfolio", dependencies=[Depends(verify_api_key)])
async def analyze_portfolio_sustainability(request: SustainabilityAnalysisRequest):
    """
    Analyze dividend sustainability of entire portfolio
    
    Returns weighted scores, grades, and risk alerts
    """
    try:
        result = sustainability_analyzer.analyze_portfolio_sustainability(request.user_id)
        return result
    except Exception as e:
        logger.error(f"Error in portfolio sustainability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cashflow/sensitivity", dependencies=[Depends(verify_api_key)])
async def analyze_cashflow_sensitivity(request: CashFlowSensitivityRequest):
    """
    Run stress tests on portfolio cash flow
    
    Analyzes impact of dividend cuts, sector downturns, and other scenarios
    """
    try:
        holdings = data_extractor.get_portfolio_holdings(request.user_id)
        result = cashflow_model.analyze_cash_flow_sensitivity(
            holdings,
            request.custom_scenarios
        )
        return result
    except Exception as e:
        logger.error(f"Error in cashflow sensitivity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", dependencies=[Depends(verify_api_key)])
async def financial_models_health():
    """Health check for financial models service"""
    return {
        'status': 'healthy',
        'service': 'financial-models',
        'engines': {
            'portfolio_projection': 'operational',
            'watchlist_projection': 'operational',
            'sustainability_analyzer': 'operational',
            'cashflow_sensitivity': 'operational'
        },
        'version': '1.0.0'
    }
