"""
Portfolio Projection Engine
Computes 1/3/5/10 year dividend income projections for user's portfolio
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


class PortfolioProjectionEngine:
    """
    Custom financial computation engine for portfolio dividend projections
    Uses real dividend history to model future income with growth assumptions
    """
    
    def __init__(self, data_extractor):
        self.data_extractor = data_extractor
    
    def calculate_dividend_growth_rate(self, dividend_history: List[Dict], method='cagr') -> float:
        """
        Calculate dividend growth rate from historical data
        Methods: 'cagr' (compound annual growth rate) or 'avg' (average year-over-year)
        """
        if len(dividend_history) < 8:
            return 3.0
        
        annual_dividends = {}
        for div in dividend_history:
            year = div['ex_date'].year if hasattr(div['ex_date'], 'year') else datetime.now().year
            annual_dividends[year] = annual_dividends.get(year, 0) + float(div['dividend_amount'] or 0)
        
        years = sorted(annual_dividends.keys())
        if len(years) < 2:
            return 3.0
        
        if method == 'cagr':
            first_year_div = annual_dividends[years[0]]
            last_year_div = annual_dividends[years[-1]]
            num_years = years[-1] - years[0]
            
            if first_year_div > 0 and num_years > 0:
                cagr = (pow(last_year_div / first_year_div, 1/num_years) - 1) * 100
                return max(min(cagr, 15.0), -5.0)
        
        elif method == 'avg':
            yoy_growth = []
            for i in range(1, len(years)):
                prev = annual_dividends[years[i-1]]
                curr = annual_dividends[years[i]]
                if prev > 0:
                    growth = ((curr - prev) / prev) * 100
                    yoy_growth.append(growth)
            
            if yoy_growth:
                avg_growth = statistics.mean(yoy_growth)
                return max(min(avg_growth, 15.0), -5.0)
        
        return 3.0
    
    def project_dividend_income(
        self, 
        holdings: List[Dict[str, Any]], 
        years: int = 10
    ) -> Dict[str, Any]:
        """
        Project dividend income for user's portfolio over N years
        
        Returns:
        {
            'current_annual_income': float,
            'projections': {
                1: {'income': X, 'total_dividends': Y, 'avg_yield': Z},
                3: {...},
                5: {...},
                10: {...}
            },
            'holdings_detail': [...],
            'growth_assumptions': {...}
        }
        """
        current_annual_income = 0
        holdings_detail = []
        
        for holding in holdings:
            ticker = holding['ticker']
            shares = float(holding['shares'])
            current_price = float(holding.get('current_price', 0) or 0)
            annual_dividend = float(holding.get('annual_dividend', 0) or 0)
            current_yield = float(holding.get('current_yield_pct', 0) or 0)
            
            dividend_history = self.data_extractor.get_dividend_history(ticker, years=10)
            growth_rate = self.calculate_dividend_growth_rate(dividend_history)
            
            current_dividend_income = shares * annual_dividend
            current_annual_income += current_dividend_income
            
            holdings_detail.append({
                'ticker': ticker,
                'shares': shares,
                'current_price': current_price,
                'annual_dividend_per_share': annual_dividend,
                'current_dividend_income': current_dividend_income,
                'current_yield_pct': current_yield,
                'estimated_growth_rate_pct': round(growth_rate, 2),
                'market_value': shares * current_price
            })
        
        projections = {}
        for year in [1, 3, 5, 10]:
            if year <= years:
                year_income = sum(
                    h['current_dividend_income'] * pow(1 + h['estimated_growth_rate_pct']/100, year)
                    for h in holdings_detail
                )
                
                total_market_value = sum(h['market_value'] for h in holdings_detail)
                avg_yield = (year_income / total_market_value * 100) if total_market_value > 0 else 0
                
                projections[year] = {
                    'annual_income': round(year_income, 2),
                    'monthly_income': round(year_income / 12, 2),
                    'avg_portfolio_yield_pct': round(avg_yield, 2),
                    'total_dividends_cumulative': round(
                        sum(
                            h['current_dividend_income'] * sum(
                                pow(1 + h['estimated_growth_rate_pct']/100, y) 
                                for y in range(1, year+1)
                            )
                            for h in holdings_detail
                        ), 2
                    )
                }
        
        total_market_value = sum(h['market_value'] for h in holdings_detail)
        
        return {
            'current_annual_income': round(current_annual_income, 2),
            'current_monthly_income': round(current_annual_income / 12, 2),
            'current_portfolio_value': round(total_market_value, 2),
            'current_avg_yield_pct': round(
                (current_annual_income / total_market_value * 100) if total_market_value > 0 else 0, 
                2
            ),
            'projections': projections,
            'holdings_detail': holdings_detail,
            'growth_assumptions': {
                'avg_growth_rate_pct': round(
                    statistics.mean([h['estimated_growth_rate_pct'] for h in holdings_detail]) 
                    if holdings_detail else 0, 2
                ),
                'method': 'CAGR from historical dividend data',
                'horizon_years': years
            },
            'summary': {
                'total_holdings': len(holdings_detail),
                'income_growth_1yr_pct': round(
                    ((projections.get(1, {}).get('annual_income', 0) - current_annual_income) / current_annual_income * 100)
                    if current_annual_income > 0 else 0, 2
                ),
                'income_growth_10yr_pct': round(
                    ((projections.get(10, {}).get('annual_income', 0) - current_annual_income) / current_annual_income * 100)
                    if current_annual_income > 0 else 0, 2
                )
            }
        }
    
    def analyze_portfolio(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point: Analyze user's portfolio and project future income
        """
        holdings = self.data_extractor.get_portfolio_holdings(user_id)
        
        if not holdings:
            return {
                'success': False,
                'error': 'No portfolio holdings found',
                'message': 'Please add stocks to your portfolio to see projections'
            }
        
        projections = self.project_dividend_income(holdings, years=10)
        
        tickers = [h['ticker'] for h in holdings]
        sector_allocation = self.data_extractor.get_sector_allocation(tickers)
        
        return {
            'success': True,
            'portfolio_projection': projections,
            'diversification': {
                'sector_allocation': sector_allocation,
                'concentration_risk': max(sector_allocation.values()) if sector_allocation else 0
            },
            'timestamp': datetime.now().isoformat()
        }
