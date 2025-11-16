"""
Dividend Lists Routes - API endpoints for curated dividend categories
Endpoints for 30+ dividend list categories and watchlist/portfolio integration
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from pydantic import BaseModel
import logging
import os

from app.core.database import engine
from app.services.dividend_list_service import DividendListService
from app.services.watchlist_portfolio_service import WatchlistPortfolioService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dividend-lists", tags=["dividend-lists"])

def get_db_connection():
    """Get database connection"""
    # Return SQLAlchemy connection instead of pymssql
    return engine.raw_connection()

def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Extract user ID from header"""
    if not x_user_id:
        return 1  # Default user for testing
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

class CategoryListResponse(BaseModel):
    category_id: str
    name: str
    description: str
    criteria: str

class StockResponse(BaseModel):
    ticker: str
    company_name: Optional[str]
    current_price: float
    dividend_yield: float
    annual_dividend: float
    payout_ratio: Optional[float]
    consecutive_years: int
    payment_frequency: Optional[str]
    sector: Optional[str]

class AddToWatchlistRequest(BaseModel):
    category_id: str
    max_stocks: Optional[int] = 10

class CreateListRequest(BaseModel):
    list_name: str
    tickers: List[str]

@router.get("/categories", response_model=List[CategoryListResponse])
async def get_all_categories():
    """
    Get all available dividend list categories
    
    Returns:
        List of all 30+ dividend categories
    """
    try:
        db = get_db_connection()
        service = DividendListService(db)
        categories = service.get_all_categories()
        db.close()
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/{category_id}", response_model=List[StockResponse])
async def get_category_stocks(category_id: str, limit: int = 50):
    """
    Get stocks for a specific dividend category
    
    Args:
        category_id: Category identifier (e.g., 'dividend_aristocrats')
        limit: Maximum number of stocks to return
        
    Returns:
        List of stocks matching the category criteria
    """
    try:
        db = get_db_connection()
        service = DividendListService(db)
        stocks = service.get_category_stocks(category_id, limit)
        db.close()
        
        if not stocks:
            raise HTTPException(status_code=404, detail="Category not found or no stocks available")
        
        return stocks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching category stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-to-watchlist")
async def add_category_to_watchlist(
    request: AddToWatchlistRequest,
    user_id: int = Depends(get_user_id_from_header)
):
    """
    Add top stocks from a category to user's watchlist
    
    Args:
        request: Category ID and max stocks to add
        user_id: User identifier from header
        
    Returns:
        Result with number of stocks added
    """
    try:
        db = get_db_connection()
        service = DividendListService(db)
        
        result = service.add_category_to_watchlist(
            user_id=user_id,
            category_id=request.category_id,
            max_stocks=request.max_stocks
        )
        
        db.close()
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding category to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/lists")
async def get_user_lists(user_id: int = Depends(get_user_id_from_header)):
    """
    Get all dividend lists for a user
    
    Args:
        user_id: User identifier from header
        
    Returns:
        List of user's custom dividend lists
    """
    try:
        db = get_db_connection()
        service = DividendListService(db)
        lists = service.get_user_lists(user_id)
        db.close()
        
        return {"lists": lists, "total": len(lists)}
        
    except Exception as e:
        logger.error(f"Error fetching user lists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/create")
async def create_custom_list(
    request: CreateListRequest,
    user_id: int = Depends(get_user_id_from_header)
):
    """
    Create a custom dividend list
    
    Args:
        request: List name and tickers
        user_id: User identifier from header
        
    Returns:
        Created list details
    """
    try:
        db = get_db_connection()
        service = DividendListService(db)
        
        result = service.create_custom_list(
            user_id=user_id,
            list_name=request.list_name,
            tickers=request.tickers
        )
        
        db.close()
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlist")
async def get_watchlist(user_id: int = Depends(get_user_id_from_header)):
    """
    Get user's watchlist with dividend data
    
    Args:
        user_id: User identifier from header
        
    Returns:
        Watchlist stocks with dividend information
    """
    try:
        db = get_db_connection()
        service = WatchlistPortfolioService(db)
        watchlist = service.get_watchlist(user_id)
        db.close()
        
        return {"watchlist": watchlist, "total": len(watchlist)}
        
    except Exception as e:
        logger.error(f"Error fetching watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
async def get_portfolio(user_id: int = Depends(get_user_id_from_header)):
    """
    Get user's portfolio with dividend projections
    
    Args:
        user_id: User identifier from header
        
    Returns:
        Portfolio positions with income projections
    """
    try:
        db = get_db_connection()
        service = WatchlistPortfolioService(db)
        portfolio = service.get_portfolio(user_id)
        summary = service.get_portfolio_summary(user_id)
        db.close()
        
        return {
            "portfolio": portfolio,
            "summary": summary,
            "total_positions": len(portfolio)
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
