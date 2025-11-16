"""
Watchlist & Portfolio Service - Integration layer for dividend lists
Manages synchronization between dividend lists and user watchlists/portfolios
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class WatchlistPortfolioService:
    """
    Service to manage watchlist and portfolio integrations with dividend lists
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_watchlist(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's watchlist with dividend data"""
        try:
            with self.db.cursor(as_dict=True) as cursor:
                cursor.execute("""
                    SELECT 
                        w.ticker,
                        w.added_date,
                        s.company_name,
                        s.current_price,
                        s.dividend_yield,
                        s.annual_dividend,
                        s.payout_ratio,
                        s.sector
                    FROM user_watchlist w
                    LEFT JOIN stock_profiles s ON w.ticker = s.ticker
                    WHERE w.user_id = %s
                    ORDER BY w.added_date DESC
                """, (user_id,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error fetching watchlist: {e}")
            return []
    
    def add_to_watchlist(self, user_id: int, ticker: str) -> Dict[str, Any]:
        """Add a ticker to user's watchlist"""
        try:
            with self.db.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_watchlist (user_id, ticker, added_date)
                    VALUES (%s, %s, %s)
                """, (user_id, ticker.upper(), datetime.now()))
                
                self.db.commit()
            
            return {"success": True, "ticker": ticker.upper()}
            
        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def remove_from_watchlist(self, user_id: int, ticker: str) -> Dict[str, Any]:
        """Remove a ticker from user's watchlist"""
        try:
            with self.db.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM user_watchlist
                    WHERE user_id = %s AND ticker = %s
                """, (user_id, ticker.upper()))
                
                self.db.commit()
            
            return {"success": True, "ticker": ticker.upper()}
            
        except Exception as e:
            logger.error(f"Error removing from watchlist: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_portfolio(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's portfolio with dividend projections"""
        try:
            with self.db.cursor(as_dict=True) as cursor:
                cursor.execute("""
                    SELECT 
                        p.ticker,
                        p.shares,
                        p.cost_basis,
                        p.purchase_date,
                        s.company_name,
                        s.current_price,
                        s.dividend_yield,
                        s.annual_dividend,
                        s.payment_frequency,
                        (p.shares * s.annual_dividend) as projected_annual_income,
                        (p.shares * s.current_price) as current_value,
                        ((p.shares * s.current_price) - (p.shares * p.cost_basis)) as unrealized_gain
                    FROM user_portfolio p
                    LEFT JOIN stock_profiles s ON p.ticker = s.ticker
                    WHERE p.user_id = %s
                    ORDER BY projected_annual_income DESC
                """, (user_id,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            return []
    
    def add_to_portfolio(self, user_id: int, ticker: str, shares: float, cost_basis: float) -> Dict[str, Any]:
        """Add a position to user's portfolio"""
        try:
            with self.db.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_portfolio (user_id, ticker, shares, cost_basis, purchase_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, ticker.upper(), shares, cost_basis, datetime.now()))
                
                self.db.commit()
            
            return {"success": True, "ticker": ticker.upper(), "shares": shares}
            
        except Exception as e:
            logger.error(f"Error adding to portfolio: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary statistics for user's portfolio"""
        try:
            portfolio = self.get_portfolio(user_id)
            
            if not portfolio:
                return {
                    "total_value": 0,
                    "total_annual_income": 0,
                    "average_yield": 0,
                    "position_count": 0
                }
            
            total_value = sum(float(p.get("current_value", 0)) for p in portfolio)
            total_income = sum(float(p.get("projected_annual_income", 0)) for p in portfolio)
            
            return {
                "total_value": round(total_value, 2),
                "total_annual_income": round(total_income, 2),
                "average_yield": round((total_income / total_value * 100) if total_value > 0 else 0, 2),
                "position_count": len(portfolio),
                "monthly_income": round(total_income / 12, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio summary: {e}")
            return {"error": str(e)}
    
    def sync_list_to_watchlist(self, user_id: int, list_id: int) -> Dict[str, Any]:
        """Sync a dividend list to user's watchlist"""
        try:
            with self.db.cursor(as_dict=True) as cursor:
                # Get stocks from dividend list
                cursor.execute("""
                    SELECT ticker FROM dividend_list_stocks WHERE list_id = %s
                """, (list_id,))
                
                stocks = cursor.fetchall()
                added = 0
                
                for stock in stocks:
                    try:
                        cursor.execute("""
                            INSERT INTO user_watchlist (user_id, ticker, added_date)
                            VALUES (%s, %s, %s)
                        """, (user_id, stock["ticker"], datetime.now()))
                        added += 1
                    except:
                        continue  # Skip duplicates
                
                self.db.commit()
            
            return {
                "success": True,
                "stocks_added": added,
                "total_stocks": len(stocks)
            }
            
        except Exception as e:
            logger.error(f"Error syncing list to watchlist: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
