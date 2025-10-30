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
        Falls back to mock data if database is unavailable.
        
        Returns:
            List of stocks with ticker, sector, dividend info, and current price
        """
        sector_placeholders = ','.join([f"'{sector}'" for sector in cls.SECTORS])
        
        query = text(f"""
            WITH HighQualityDividends AS (
                SELECT 
                    Ticker,
                    AdjDividend_Amount,
                    Payment_Date,
                    Confidence_Score,
                    Data_Source,
                    ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Payment_Date DESC) AS rn
                FROM dbo.vDividendsEnhanced
                WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
                    AND AdjDividend_Amount > 0
                    AND Confidence_Score >= 0.7
            ),
            AnnualDividends AS (
                SELECT 
                    Ticker,
                    SUM(AdjDividend_Amount) AS annual_dividend,
                    MAX(Confidence_Score) AS max_confidence,
                    MAX(Data_Source) AS primary_source
                FROM dbo.vDividendsEnhanced
                WHERE Payment_Date >= DATEADD(year, -1, CAST(GETDATE() AS DATE))
                    AND AdjDividend_Amount > 0
                    AND Confidence_Score >= 0.7
                GROUP BY Ticker
            ),
            LatestPrices AS (
                SELECT 
                    Ticker,
                    Price,
                    Market_Cap,
                    ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Last_Updated DESC) AS rn
                FROM dbo.vQuotesEnhanced
                WHERE Price > 0
            )
            SELECT TOP {limit}
                s.Ticker,
                s.Company_Name,
                s.Sector,
                'Stock' AS Security_Type,
                ad.annual_dividend,
                p.Price,
                (ad.annual_dividend / NULLIF(p.Price, 0) * 100) AS dividend_yield_pct,
                ad.max_confidence AS confidence_score,
                ad.primary_source AS data_source
            FROM dbo.vSecurities s
            INNER JOIN AnnualDividends ad ON s.Ticker = ad.Ticker
            INNER JOIN LatestPrices p ON s.Ticker = p.Ticker AND p.rn = 1
            WHERE s.Sector IN ({sector_placeholders})
                AND p.Price > 0
                AND ad.annual_dividend > 0
                AND (ad.annual_dividend / NULLIF(p.Price, 0)) > 0.02
            ORDER BY dividend_yield_pct DESC
        """)
        
        try:
            with engine.connect() as conn:
                result = conn.execute(query)
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
                
                if stocks:
                    return stocks
                else:
                    logger.warning("Database returned no dividend stocks, using mock data fallback")
                    return cls._get_mock_dividend_stocks(limit)
                
        except Exception as e:
            logger.error(f"Error querying dividend stocks: {e}, using mock data fallback", exc_info=True)
            return cls._get_mock_dividend_stocks(limit)
    
    @classmethod
    def _get_mock_dividend_stocks(cls, limit: int = 20) -> List[Dict]:
        """
        Return realistic mock dividend stock data as fallback.
        
        Returns:
            List of mock dividend stocks with realistic yields
        """
        mock_stocks = [
            {"ticker": "VZ", "company_name": "Verizon Communications Inc", "sector": "Communication Services", "security_type": "Stock", "annual_dividend": 2.61, "price": 38.15, "dividend_yield_pct": 6.84},
            {"ticker": "T", "company_name": "AT&T Inc", "sector": "Communication Services", "security_type": "Stock", "annual_dividend": 1.11, "price": 21.25, "dividend_yield_pct": 5.22},
            {"ticker": "MO", "company_name": "Altria Group Inc", "sector": "Consumer Staples", "security_type": "Stock", "annual_dividend": 3.92, "price": 48.75, "dividend_yield_pct": 8.04},
            {"ticker": "SO", "company_name": "Southern Company", "sector": "Utilities", "security_type": "Stock", "annual_dividend": 2.80, "price": 78.50, "dividend_yield_pct": 3.57},
            {"ticker": "DUK", "company_name": "Duke Energy Corporation", "sector": "Utilities", "security_type": "Stock", "annual_dividend": 4.02, "price": 98.20, "dividend_yield_pct": 4.09},
            {"ticker": "XOM", "company_name": "Exxon Mobil Corporation", "sector": "Energy", "security_type": "Stock", "annual_dividend": 3.64, "price": 112.45, "dividend_yield_pct": 3.24},
            {"ticker": "CVX", "company_name": "Chevron Corporation", "sector": "Energy", "security_type": "Stock", "annual_dividend": 6.04, "price": 158.30, "dividend_yield_pct": 3.82},
            {"ticker": "O", "company_name": "Realty Income Corporation", "sector": "Real Estate", "security_type": "Stock", "annual_dividend": 3.06, "price": 56.80, "dividend_yield_pct": 5.39},
            {"ticker": "VICI", "company_name": "VICI Properties Inc", "sector": "Real Estate", "security_type": "Stock", "annual_dividend": 1.58, "price": 31.45, "dividend_yield_pct": 5.02},
            {"ticker": "JPM", "company_name": "JPMorgan Chase & Co", "sector": "Financials", "security_type": "Stock", "annual_dividend": 4.20, "price": 165.75, "dividend_yield_pct": 2.53},
            {"ticker": "BAC", "company_name": "Bank of America Corp", "sector": "Financials", "security_type": "Stock", "annual_dividend": 0.96, "price": 32.15, "dividend_yield_pct": 2.99},
            {"ticker": "JNJ", "company_name": "Johnson & Johnson", "sector": "Healthcare", "security_type": "Stock", "annual_dividend": 4.76, "price": 158.90, "dividend_yield_pct": 3.00},
            {"ticker": "PFE", "company_name": "Pfizer Inc", "sector": "Healthcare", "security_type": "Stock", "annual_dividend": 1.68, "price": 28.50, "dividend_yield_pct": 5.89},
            {"ticker": "MMM", "company_name": "3M Company", "sector": "Industrials", "security_type": "Stock", "annual_dividend": 6.00, "price": 89.20, "dividend_yield_pct": 6.73},
            {"ticker": "CAT", "company_name": "Caterpillar Inc", "sector": "Industrials", "security_type": "Stock", "annual_dividend": 5.20, "price": 285.40, "dividend_yield_pct": 1.82},
            {"ticker": "KO", "company_name": "The Coca-Cola Company", "sector": "Consumer Staples", "security_type": "Stock", "annual_dividend": 1.84, "price": 62.30, "dividend_yield_pct": 2.95},
            {"ticker": "PEP", "company_name": "PepsiCo Inc", "sector": "Consumer Staples", "security_type": "Stock", "annual_dividend": 5.06, "price": 168.75, "dividend_yield_pct": 3.00},
            {"ticker": "NEE", "company_name": "NextEra Energy Inc", "sector": "Utilities", "security_type": "Stock", "annual_dividend": 1.86, "price": 78.90, "dividend_yield_pct": 2.36},
            {"ticker": "D", "company_name": "Dominion Energy Inc", "sector": "Utilities", "security_type": "Stock", "annual_dividend": 2.67, "price": 52.45, "dividend_yield_pct": 5.09},
            {"ticker": "PSA", "company_name": "Public Storage", "sector": "Real Estate", "security_type": "Stock", "annual_dividend": 12.00, "price": 298.50, "dividend_yield_pct": 4.02},
        ]
        
        return mock_stocks[:limit]
    
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
