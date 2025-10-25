"""
Passive Income Planning Service
Generates diversified dividend portfolio plans based on user goals.
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)


class PassiveIncomePlanService:
    """Service for generating passive income portfolio plans."""
    
    DIVIDEND_YIELDS = {
        "conservative": 0.035,
        "moderate": 0.045,
        "aggressive": 0.055
    }
    
    DIVIDEND_GROWTH_RATE = 0.03
    
    SECTORS = [
        "Utilities",
        "Real Estate",
        "Energy",
        "Consumer Staples",
        "Financials",
        "Healthcare",
        "Industrials",
        "Communication Services"
    ]
    
    @classmethod
    def generate_plan(
        cls,
        target_annual_income: float = 100000.0,
        years: int = 5,
        risk_tolerance: str = "moderate"
    ) -> Dict:
        """
        Generate a passive income portfolio plan.
        
        Args:
            target_annual_income: Target annual dividend income
            years: Investment time horizon
            risk_tolerance: "conservative", "moderate", or "aggressive"
            
        Returns:
            Dict with plan summary, allocations, projections, and diversification
        """
        try:
            risk_tolerance = risk_tolerance.lower()
            if risk_tolerance not in cls.DIVIDEND_YIELDS:
                risk_tolerance = "moderate"
            
            avg_yield = cls.DIVIDEND_YIELDS[risk_tolerance]
            required_capital = target_annual_income / avg_yield
            
            top_dividend_stocks = cls._query_top_dividend_stocks(limit=20)
            
            allocations = cls._build_diversified_portfolio(
                top_dividend_stocks,
                required_capital,
                risk_tolerance
            )
            
            projections = cls._calculate_income_projections(
                allocations,
                years
            )
            
            diversification = cls._calculate_sector_diversification(allocations)
            
            return {
                "success": True,
                "summary": {
                    "target_annual_income": target_annual_income,
                    "required_capital": required_capital,
                    "avg_dividend_yield": avg_yield * 100,
                    "risk_tolerance": risk_tolerance,
                    "years": years,
                    "num_holdings": len(allocations)
                },
                "assumptions": {
                    "dividend_yield": f"{avg_yield * 100:.2f}%",
                    "annual_dividend_growth": f"{cls.DIVIDEND_GROWTH_RATE * 100:.1f}%",
                    "risk_profile": risk_tolerance
                },
                "allocations": allocations,
                "projections": projections,
                "diversification": diversification
            }
            
        except Exception as e:
            logger.error(f"Error generating passive income plan: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "summary": {},
                "assumptions": {},
                "allocations": [],
                "projections": [],
                "diversification": {}
            }
    
    @classmethod
    def _query_top_dividend_stocks(cls, limit: int = 20) -> List[Dict]:
        """
        Query database for top dividend-paying stocks and ETFs.
        
        Returns:
            List of stocks with ticker, sector, dividend info, and current price
        """
        sector_placeholders = ','.join([f"'{sector}'" for sector in cls.SECTORS])
        
        query = text(f"""
            WITH LatestDividends AS (
                SELECT 
                    Ticker,
                    AdjDividend_Amount,
                    Payment_Date,
                    ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Payment_Date DESC) AS rn
                FROM dbo.vDividends
                WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
                    AND AdjDividend_Amount > 0
            ),
            AnnualDividends AS (
                SELECT 
                    Ticker,
                    SUM(AdjDividend_Amount) AS annual_dividend
                FROM dbo.vDividends
                WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
                    AND AdjDividend_Amount > 0
                GROUP BY Ticker
            ),
            LatestPrices AS (
                SELECT 
                    Ticker,
                    Price,
                    ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY 
                        COALESCE(Trade_Timestamp_UTC, Snapshot_Timestamp) DESC) AS rn
                FROM dbo.vPrices
                WHERE Price > 0
            )
            SELECT TOP :limit
                t.Ticker,
                t.Company_Name,
                t.Sector,
                t.Security_Type,
                ad.annual_dividend,
                p.Price,
                (ad.annual_dividend / NULLIF(p.Price, 0) * 100) AS dividend_yield_pct
            FROM dbo.vTickers t
            INNER JOIN AnnualDividends ad ON t.Ticker = ad.Ticker
            INNER JOIN LatestPrices p ON t.Ticker = p.Ticker AND p.rn = 1
            WHERE t.Sector IN ({sector_placeholders})
                AND p.Price > 0
                AND ad.annual_dividend > 0
                AND (ad.annual_dividend / NULLIF(p.Price, 0)) > 0.02
            ORDER BY dividend_yield_pct DESC
        """)
        
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"limit": limit}
                )
                rows = result.fetchall()
                
                stocks = []
                for row in rows:
                    stocks.append({
                        "ticker": row[0],
                        "company_name": row[1],
                        "sector": row[2] or "Other",
                        "security_type": row[3],
                        "annual_dividend": float(row[4]) if row[4] else 0.0,
                        "price": float(row[5]) if row[5] else 0.0,
                        "dividend_yield_pct": float(row[6]) if row[6] else 0.0
                    })
                
                return stocks
                
        except Exception as e:
            logger.error(f"Error querying dividend stocks: {e}", exc_info=True)
            return []
    
    @classmethod
    def _build_diversified_portfolio(
        cls,
        stocks: List[Dict],
        total_capital: float,
        risk_tolerance: str
    ) -> List[Dict]:
        """
        Build a diversified portfolio allocation.
        
        Args:
            stocks: List of candidate stocks
            total_capital: Total capital to allocate
            risk_tolerance: Risk profile
            
        Returns:
            List of allocation dicts with ticker, shares, cost, allocation_pct, etc.
        """
        if not stocks:
            return []
        
        sector_groups = {}
        for stock in stocks:
            sector = stock.get("sector", "Other")
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(stock)
        
        target_holdings = 10 if risk_tolerance == "moderate" else (8 if risk_tolerance == "conservative" else 12)
        
        allocations = []
        sectors_used = list(sector_groups.keys())[:target_holdings]
        allocation_per_holding = 1.0 / target_holdings
        
        for i, sector in enumerate(sectors_used):
            if i >= target_holdings:
                break
                
            sector_stocks = sector_groups[sector]
            if not sector_stocks:
                continue
            
            stock = sector_stocks[0]
            
            allocation_pct = allocation_per_holding * 100
            capital_for_position = total_capital * allocation_per_holding
            
            price = stock.get("price", 0)
            if price > 0:
                shares = capital_for_position / price
            else:
                shares = 0
            
            allocations.append({
                "ticker": stock.get("ticker"),
                "company_name": stock.get("company_name"),
                "sector": sector,
                "security_type": stock.get("security_type"),
                "shares": round(shares, 2),
                "price": price,
                "cost": round(capital_for_position, 2),
                "allocation_pct": round(allocation_pct, 2),
                "dividend_yield_pct": stock.get("dividend_yield_pct", 0),
                "annual_dividend": stock.get("annual_dividend", 0)
            })
        
        return allocations
    
    @classmethod
    def _calculate_income_projections(
        cls,
        allocations: List[Dict],
        years: int
    ) -> List[Dict]:
        """
        Calculate year-by-year dividend income projections.
        
        Args:
            allocations: Portfolio allocations
            years: Number of years to project
            
        Returns:
            List of yearly projection dicts
        """
        projections = []
        
        total_annual_dividend = sum(
            alloc.get("shares", 0) * alloc.get("annual_dividend", 0)
            for alloc in allocations
        )
        
        for year in range(1, years + 1):
            projected_income = total_annual_dividend * ((1 + cls.DIVIDEND_GROWTH_RATE) ** (year - 1))
            projections.append({
                "year": year,
                "projected_income": round(projected_income, 2)
            })
        
        return projections
    
    @classmethod
    def _calculate_sector_diversification(cls, allocations: List[Dict]) -> Dict:
        """
        Calculate sector allocation percentages.
        
        Args:
            allocations: Portfolio allocations
            
        Returns:
            Dict mapping sector names to allocation percentages
        """
        sector_allocation = {}
        
        for alloc in allocations:
            sector = alloc.get("sector", "Other")
            pct = alloc.get("allocation_pct", 0)
            
            if sector in sector_allocation:
                sector_allocation[sector] += pct
            else:
                sector_allocation[sector] = pct
        
        return {k: round(v, 2) for k, v in sector_allocation.items()}
