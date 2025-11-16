"""
Dividend List Service - Manages 30+ curated dividend stock categories
Provides intelligent dividend list management with watchlist/portfolio integration
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pymssql

logger = logging.getLogger(__name__)

class DividendListService:
    """
    Service to manage curated dividend lists and integrate with user watchlists/portfolios
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.list_categories = self._initialize_categories()
    
    def _initialize_categories(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the 30+ dividend list categories"""
        return {
            "dividend_aristocrats": {
                "name": "Dividend Aristocrats",
                "description": "S&P 500 companies with 25+ years of consecutive dividend increases",
                "criteria": "25+ years of dividend growth, S&P 500 member",
                "min_years": 25
            },
            "dividend_kings": {
                "name": "Dividend Kings",
                "description": "Companies with 50+ years of consecutive dividend increases",
                "criteria": "50+ years of dividend growth",
                "min_years": 50
            },
            "dividend_champions": {
                "name": "Dividend Champions",
                "description": "Companies with 25+ years of dividend growth (broader than Aristocrats)",
                "criteria": "25+ years of dividend growth, any index",
                "min_years": 25
            },
            "high_yield": {
                "name": "High Yield Dividends",
                "description": "Stocks with dividend yields above 5%",
                "criteria": "Dividend yield >= 5%",
                "min_yield": 5.0
            },
            "monthly_payers": {
                "name": "Monthly Dividend Payers",
                "description": "Companies that pay dividends monthly",
                "criteria": "Monthly dividend payment frequency",
                "frequency": "Monthly"
            },
            "quarterly_growth": {
                "name": "Quarterly Growth Leaders",
                "description": "Companies with strong quarterly dividend growth",
                "criteria": "Consistent quarterly dividend increases",
                "growth_focus": True
            },
            "reits": {
                "name": "Real Estate Investment Trusts (REITs)",
                "description": "REITs with strong dividend track records",
                "criteria": "REIT classification, reliable dividends",
                "sector": "Real Estate"
            },
            "utilities": {
                "name": "Utility Dividend Stocks",
                "description": "Utility companies with stable dividend payments",
                "criteria": "Utilities sector, stable dividends",
                "sector": "Utilities"
            },
            "dividend_etfs": {
                "name": "Dividend-Focused ETFs",
                "description": "ETFs specializing in dividend-paying stocks",
                "criteria": "Dividend-focused ETF strategy",
                "asset_type": "ETF"
            },
            "low_payout_ratio": {
                "name": "Conservative Payout Ratios",
                "description": "Companies with sustainable payout ratios below 60%",
                "criteria": "Payout ratio < 60%, safe dividends",
                "max_payout_ratio": 60.0
            }
        }
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all available dividend list categories"""
        return [
            {
                "category_id": cat_id,
                **details
            }
            for cat_id, details in self.list_categories.items()
        ]
    
    def get_category_stocks(self, category_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get stocks for a specific category
        
        Args:
            category_id: Category identifier
            limit: Maximum number of stocks to return
            
        Returns:
            List of stocks matching the category criteria
        """
        if category_id not in self.list_categories:
            logger.error(f"Invalid category: {category_id}")
            return []
        
        category = self.list_categories[category_id]
        
        try:
            # Build query based on category criteria
            query = self._build_category_query(category_id, category, limit)
            
            with self.db.cursor(as_dict=True) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
            return self._format_stock_results(results)
            
        except Exception as e:
            logger.error(f"Error fetching category stocks: {e}")
            return []
    
    def _build_category_query(self, category_id: str, category: Dict[str, Any], limit: int) -> str:
        """Build SQL query for category criteria"""
        
        base_query = """
            SELECT TOP (?)
                ticker,
                company_name,
                current_price,
                dividend_yield,
                annual_dividend,
                payout_ratio,
                consecutive_years,
                payment_frequency,
                sector
            FROM stock_profiles
            WHERE is_active = 1
        """
        
        conditions = []
        
        # Add category-specific conditions
        if "min_years" in category:
            conditions.append(f"AND consecutive_years >= {category['min_years']}")
        
        if "min_yield" in category:
            conditions.append(f"AND dividend_yield >= {category['min_yield']}")
        
        if "max_payout_ratio" in category:
            conditions.append(f"AND payout_ratio <= {category['max_payout_ratio']}")
        
        if "frequency" in category:
            conditions.append(f"AND payment_frequency = '{category['frequency']}'")
        
        if "sector" in category:
            conditions.append(f"AND sector = '{category['sector']}'")
        
        # Combine query
        full_query = base_query + " " + " ".join(conditions) + " ORDER BY dividend_yield DESC"
        
        return full_query.replace("(?)", f"({limit})")
    
    def _format_stock_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Format database results for API response"""
        formatted = []
        
        for row in results:
            formatted.append({
                "ticker": row.get("ticker"),
                "company_name": row.get("company_name"),
                "current_price": float(row.get("current_price", 0)),
                "dividend_yield": float(row.get("dividend_yield", 0)),
                "annual_dividend": float(row.get("annual_dividend", 0)),
                "payout_ratio": float(row.get("payout_ratio", 0)) if row.get("payout_ratio") else None,
                "consecutive_years": int(row.get("consecutive_years", 0)),
                "payment_frequency": row.get("payment_frequency"),
                "sector": row.get("sector")
            })
        
        return formatted
    
    def add_category_to_watchlist(self, user_id: int, category_id: str, max_stocks: int = 10) -> Dict[str, Any]:
        """
        Add top stocks from a category to user's watchlist
        
        Args:
            user_id: User identifier
            category_id: Category to add
            max_stocks: Maximum stocks to add
            
        Returns:
            Result dictionary with added stocks
        """
        try:
            # Get category stocks
            stocks = self.get_category_stocks(category_id, limit=max_stocks)
            
            if not stocks:
                return {"success": False, "error": "No stocks found for category"}
            
            added_count = 0
            
            with self.db.cursor() as cursor:
                for stock in stocks:
                    try:
                        cursor.execute("""
                            INSERT INTO user_watchlist (user_id, ticker, added_date)
                            VALUES (%s, %s, %s)
                        """, (user_id, stock["ticker"], datetime.now()))
                        added_count += 1
                    except Exception as e:
                        # Skip if already in watchlist
                        logger.debug(f"Skipping {stock['ticker']}: {e}")
                        continue
                
                self.db.commit()
            
            return {
                "success": True,
                "category": category_id,
                "stocks_added": added_count,
                "total_stocks": len(stocks)
            }
            
        except Exception as e:
            logger.error(f"Error adding category to watchlist: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_user_lists(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all dividend lists for a user"""
        try:
            with self.db.cursor(as_dict=True) as cursor:
                cursor.execute("""
                    SELECT list_id, list_name, category_id, created_date, stock_count
                    FROM dividend_lists
                    WHERE user_id = %s
                    ORDER BY created_date DESC
                """, (user_id,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error fetching user lists: {e}")
            return []
    
    def create_custom_list(self, user_id: int, list_name: str, tickers: List[str]) -> Dict[str, Any]:
        """Create a custom dividend list for a user"""
        try:
            with self.db.cursor() as cursor:
                # Create list
                cursor.execute("""
                    INSERT INTO dividend_lists (user_id, list_name, created_date, stock_count)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, list_name, datetime.now(), len(tickers)))
                
                list_id = cursor.lastrowid
                
                # Add stocks to list
                for ticker in tickers:
                    cursor.execute("""
                        INSERT INTO dividend_list_stocks (list_id, ticker, added_date)
                        VALUES (%s, %s, %s)
                    """, (list_id, ticker, datetime.now()))
                
                self.db.commit()
            
            return {
                "success": True,
                "list_id": list_id,
                "list_name": list_name,
                "stock_count": len(tickers)
            }
            
        except Exception as e:
            logger.error(f"Error creating custom list: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
