"""
Database utilities for financial model data extraction
Uses SQLAlchemy with Harvey's existing database connection
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import text

logger = logging.getLogger(__name__)

class FinancialDataExtractor:
    """Extract portfolio and dividend data from Azure SQL for financial computations"""
    
    def __init__(self, engine=None):
        """
        Initialize with SQLAlchemy engine
        If no engine provided, uses Harvey's default database engine
        """
        if engine is None:
            from app.core.database import engine as default_engine
            self.engine = default_engine
        else:
            self.engine = engine
    
    def get_portfolio_holdings(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get user's portfolio holdings with current prices and dividend info
        Returns: List of holdings with {ticker, shares, cost_basis, current_price, current_yield}
        """
        query_text = """
        SELECT 
            ph.ticker,
            ph.shares,
            ph.cost_basis,
            lp.price as current_price,
            lp.change_percent,
            dd.annual_dividend,
            CASE 
                WHEN lp.price > 0 THEN (dd.annual_dividend / lp.price) * 100
                ELSE 0
            END as current_yield_pct,
            t.company_name,
            t.sector,
            t.industry
        FROM portfolio_holdings ph
        LEFT JOIN latest_prices lp ON ph.ticker = lp.ticker
        LEFT JOIN (
            SELECT 
                ticker,
                SUM(dividend_amount) as annual_dividend
            FROM dividend_data
            WHERE ex_date >= DATEADD(year, -1, GETDATE())
            GROUP BY ticker
        ) dd ON ph.ticker = dd.ticker
        LEFT JOIN tickers t ON ph.ticker = t.ticker
        WHERE ph.shares > 0
        """
        
        if user_id:
            query_text += " AND ph.user_id = :user_id"
        
        try:
            with self.engine.connect() as conn:
                if user_id:
                    result = conn.execute(text(query_text), {"user_id": user_id})
                else:
                    result = conn.execute(text(query_text))
                
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to fetch portfolio holdings: {e}")
            return []
    
    def get_watchlist_stocks(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get user's watchlist with current prices and dividend info
        Returns: List of stocks with {ticker, current_price, current_yield, sector}
        """
        query_text = """
        SELECT 
            w.ticker,
            lp.price as current_price,
            lp.change_percent,
            dd.annual_dividend,
            CASE 
                WHEN lp.price > 0 THEN (dd.annual_dividend / lp.price) * 100
                ELSE 0
            END as current_yield_pct,
            t.company_name,
            t.sector,
            t.industry,
            t.dividend_yield as reported_yield
        FROM watchlist w
        LEFT JOIN latest_prices lp ON w.ticker = lp.ticker
        LEFT JOIN (
            SELECT 
                ticker,
                SUM(dividend_amount) as annual_dividend
            FROM dividend_data
            WHERE ex_date >= DATEADD(year, -1, GETDATE())
            GROUP BY ticker
        ) dd ON w.ticker = dd.ticker
        LEFT JOIN tickers t ON w.ticker = t.ticker
        WHERE 1=1
        """
        
        if user_id:
            query_text += " AND w.user_id = :user_id"
        
        try:
            with self.engine.connect() as conn:
                if user_id:
                    result = conn.execute(text(query_text), {"user_id": user_id})
                else:
                    result = conn.execute(text(query_text))
                
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to fetch watchlist: {e}")
            return []
    
    def get_dividend_history(self, ticker: str, years: int = 10) -> List[Dict[str, Any]]:
        """
        Get dividend payment history for a ticker
        Returns: List of dividend records with {ex_date, dividend_amount, payment_date}
        """
        query_text = """
        SELECT 
            ex_date,
            dividend_amount,
            payment_date,
            record_date,
            declared_date
        FROM dividend_data
        WHERE ticker = :ticker
          AND ex_date >= DATEADD(year, -:years, GETDATE())
        ORDER BY ex_date DESC
        """
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query_text), {"ticker": ticker, "years": years})
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to fetch dividend history for {ticker}: {e}")
            return []
    
    def get_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental metrics for a ticker
        Returns: Dict with {payout_ratio, pe_ratio, dividend_yield, etc.}
        """
        query_text = """
        SELECT 
            ticker,
            payout_ratio,
            pe_ratio,
            dividend_yield,
            market_cap,
            sector,
            industry,
            beta
        FROM tickers
        WHERE ticker = :ticker
        """
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query_text), {"ticker": ticker})
                row = result.fetchone()
                
                if row:
                    return dict(row._mapping)
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {ticker}: {e}")
            return None
    
    def get_sector_allocation(self, tickers: List[str]) -> Dict[str, float]:
        """
        Get sector allocation percentages for a list of tickers
        Returns: Dict of {sector: percentage}
        """
        if not tickers:
            return {}
        
        placeholders = ', '.join([f':ticker{i}' for i in range(len(tickers))])
        query_text = f"""
        SELECT 
            t.sector,
            COUNT(*) as count
        FROM tickers t
        WHERE t.ticker IN ({placeholders})
        GROUP BY t.sector
        """
        
        try:
            with self.engine.connect() as conn:
                params = {f'ticker{i}': ticker for i, ticker in enumerate(tickers)}
                result = conn.execute(text(query_text), params)
                rows = result.fetchall()
                
                total = sum(row[1] for row in rows)
                if total == 0:
                    return {}
                
                return {row[0]: (row[1] / total * 100) for row in rows}
                
        except Exception as e:
            logger.error(f"Failed to fetch sector allocation: {e}")
            return {}
