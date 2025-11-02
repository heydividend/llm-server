"""
Watchlist Projection Engine
Analyzes potential income from watchlist stocks with allocation recommendations
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class WatchlistProjectionEngine:
    """
    Analyzes watchlist stocks and projects "what if" scenarios
    Compares potential income vs. current portfolio
    """
    
    def __init__(self, data_extractor):
        self.data_extractor = data_extractor
    
    def calculate_optimal_allocation(
        self,
        watchlist_stocks: List[Dict[str, Any]],
        target_monthly_income: float,
        total_capital: float
    ) -> Dict[str, Any]:
        """
        Calculate optimal allocation to achieve target monthly income
        Using watchlist stocks with diversification constraints
        """
        if not watchlist_stocks or total_capital <= 0:
            return {'success': False, 'error': 'Invalid inputs'}
        
        valid_stocks = [
            s for s in watchlist_stocks
            if s.get('current_price', 0) > 0 and s.get('annual_dividend', 0) > 0
        ]
        
        if not valid_stocks:
            return {'success': False, 'error': 'No valid dividend-paying stocks in watchlist'}
        
        sorted_by_yield = sorted(
            valid_stocks, 
            key=lambda x: float(x.get('current_yield_pct', 0) or 0),
            reverse=True
        )
        
        target_annual_income = target_monthly_income * 12
        
        allocations = []
        remaining_capital = total_capital
        projected_annual_income = 0
        
        max_allocation_per_stock = total_capital * 0.15
        
        for stock in sorted_by_yield:
            if remaining_capital <= 0 or projected_annual_income >= target_annual_income:
                break
            
            ticker = stock['ticker']
            price = float(stock['current_price'])
            annual_div = float(stock['annual_dividend'])
            yield_pct = float(stock.get('current_yield_pct', 0) or 0)
            
            allocation = min(max_allocation_per_stock, remaining_capital)
            
            shares = int(allocation / price) if price > 0 else 0
            actual_allocation = shares * price
            annual_income = shares * annual_div
            
            if shares > 0:
                allocations.append({
                    'ticker': ticker,
                    'company_name': stock.get('company_name', ticker),
                    'shares': shares,
                    'price_per_share': round(price, 2),
                    'allocation': round(actual_allocation, 2),
                    'allocation_pct': round((actual_allocation / total_capital * 100), 2),
                    'annual_dividend_per_share': round(annual_div, 2),
                    'annual_income': round(annual_income, 2),
                    'monthly_income': round(annual_income / 12, 2),
                    'yield_pct': round(yield_pct, 2),
                    'sector': stock.get('sector', 'Unknown')
                })
                
                remaining_capital -= actual_allocation
                projected_annual_income += annual_income
        
        total_allocated = sum(a['allocation'] for a in allocations)
        
        return {
            'success': True,
            'allocations': allocations,
            'summary': {
                'total_capital': round(total_capital, 2),
                'total_allocated': round(total_allocated, 2),
                'unallocated': round(remaining_capital, 2),
                'projected_annual_income': round(projected_annual_income, 2),
                'projected_monthly_income': round(projected_annual_income / 12, 2),
                'target_monthly_income': round(target_monthly_income, 2),
                'achievement_pct': round(
                    (projected_annual_income / target_annual_income * 100) 
                    if target_annual_income > 0 else 0, 2
                ),
                'avg_portfolio_yield_pct': round(
                    (projected_annual_income / total_allocated * 100) 
                    if total_allocated > 0 else 0, 2
                ),
                'num_positions': len(allocations)
            }
        }
    
    def analyze_watchlist(
        self, 
        user_id: Optional[str] = None,
        investment_amount: float = 10000
    ) -> Dict[str, Any]:
        """
        Analyze watchlist and project potential income with given investment
        """
        watchlist = self.data_extractor.get_watchlist_stocks(user_id)
        
        if not watchlist:
            return {
                'success': False,
                'error': 'No watchlist stocks found',
                'message': 'Please add stocks to your watchlist to see projections'
            }
        
        stock_analysis = []
        for stock in watchlist:
            ticker = stock['ticker']
            price = float(stock.get('current_price', 0) or 0)
            annual_div = float(stock.get('annual_dividend', 0) or 0)
            yield_pct = float(stock.get('current_yield_pct', 0) or 0)
            
            if price > 0:
                shares_possible = int(investment_amount / price)
                potential_annual_income = shares_possible * annual_div
                
                dividend_history = self.data_extractor.get_dividend_history(ticker, years=5)
                growth_rate = self._calculate_growth_rate(dividend_history)
                
                fundamentals = self.data_extractor.get_fundamental_data(ticker)
                payout_ratio = float(fundamentals.get('payout_ratio', 0) or 0) if fundamentals else 0
                
                stock_analysis.append({
                    'ticker': ticker,
                    'company_name': stock.get('company_name', ticker),
                    'current_price': round(price, 2),
                    'current_yield_pct': round(yield_pct, 2),
                    'annual_dividend': round(annual_div, 2),
                    'shares_possible': shares_possible,
                    'potential_annual_income': round(potential_annual_income, 2),
                    'potential_monthly_income': round(potential_annual_income / 12, 2),
                    'estimated_growth_rate_pct': round(growth_rate, 2),
                    'payout_ratio_pct': round(payout_ratio, 2),
                    'sector': stock.get('sector', 'Unknown'),
                    'industry': stock.get('industry', 'Unknown'),
                    'sustainability_score': self._calculate_sustainability_score(
                        payout_ratio, growth_rate, yield_pct
                    )
                })
        
        sorted_by_score = sorted(
            stock_analysis,
            key=lambda x: x['sustainability_score'],
            reverse=True
        )
        
        tickers = [s['ticker'] for s in watchlist]
        sector_allocation = self.data_extractor.get_sector_allocation(tickers)
        
        return {
            'success': True,
            'watchlist_analysis': sorted_by_score,
            'investment_amount': investment_amount,
            'diversification': {
                'sector_allocation': sector_allocation,
                'concentration_risk': max(sector_allocation.values()) if sector_allocation else 0
            },
            'recommendations': {
                'top_picks': sorted_by_score[:5],
                'highest_yield': max(stock_analysis, key=lambda x: x['current_yield_pct']) if stock_analysis else None,
                'best_growth': max(stock_analysis, key=lambda x: x['estimated_growth_rate_pct']) if stock_analysis else None,
                'most_sustainable': max(stock_analysis, key=lambda x: x['sustainability_score']) if stock_analysis else None
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_growth_rate(self, dividend_history: List[Dict]) -> float:
        """Calculate dividend growth rate from history"""
        if len(dividend_history) < 8:
            return 3.0
        
        annual_dividends = {}
        for div in dividend_history:
            year = div['ex_date'].year if hasattr(div['ex_date'], 'year') else datetime.now().year
            annual_dividends[year] = annual_dividends.get(year, 0) + float(div['dividend_amount'] or 0)
        
        years = sorted(annual_dividends.keys())
        if len(years) < 2:
            return 3.0
        
        first_year_div = annual_dividends[years[0]]
        last_year_div = annual_dividends[years[-1]]
        num_years = years[-1] - years[0]
        
        if first_year_div > 0 and num_years > 0:
            cagr = (pow(last_year_div / first_year_div, 1/num_years) - 1) * 100
            return max(min(cagr, 15.0), -5.0)
        
        return 3.0
    
    def _calculate_sustainability_score(self, payout_ratio: float, growth_rate: float, yield_pct: float) -> float:
        """
        Calculate sustainability score (0-100)
        Factors: payout ratio health, growth rate, yield attractiveness
        """
        score = 50.0
        
        if 20 <= payout_ratio <= 70:
            score += 20
        elif payout_ratio < 20:
            score += 10
        elif payout_ratio > 100:
            score -= 20
        
        if growth_rate > 5:
            score += 15
        elif growth_rate > 0:
            score += 10
        elif growth_rate < 0:
            score -= 15
        
        if 2 <= yield_pct <= 6:
            score += 15
        elif yield_pct > 6:
            score += 5
        
        return max(min(score, 100), 0)
