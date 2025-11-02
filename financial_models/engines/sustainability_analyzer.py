"""
Dividend Sustainability Analyzer
Analyzes payout ratio health, FCF coverage, and cut risk scoring
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class DividendSustainabilityAnalyzer:
    """
    Analyzes dividend sustainability using fundamental metrics
    Provides cut risk scoring and health assessment
    """
    
    def __init__(self, data_extractor):
        self.data_extractor = data_extractor
    
    def analyze_stock_sustainability(self, ticker: str) -> Dict[str, Any]:
        """
        Comprehensive sustainability analysis for a single stock
        """
        fundamentals = self.data_extractor.get_fundamental_data(ticker)
        dividend_history = self.data_extractor.get_dividend_history(ticker, years=10)
        
        if not fundamentals:
            return {
                'success': False,
                'ticker': ticker,
                'error': 'Unable to fetch fundamental data'
            }
        
        payout_ratio = float(fundamentals.get('payout_ratio', 0) or 0)
        current_yield = float(fundamentals.get('dividend_yield', 0) or 0)
        
        payout_health = self._assess_payout_ratio(payout_ratio)
        
        consistency_score = self._calculate_consistency_score(dividend_history)
        
        growth_rate = self._calculate_growth_rate(dividend_history)
        growth_health = self._assess_growth_health(growth_rate)
        
        cut_risk_score = self._calculate_cut_risk(
            payout_ratio, consistency_score, growth_rate, current_yield
        )
        
        overall_score = (
            payout_health['score'] * 0.35 +
            consistency_score * 0.30 +
            growth_health['score'] * 0.25 +
            (100 - cut_risk_score) * 0.10
        )
        
        return {
            'success': True,
            'ticker': ticker,
            'sustainability_analysis': {
                'overall_score': round(overall_score, 1),
                'grade': self._score_to_grade(overall_score),
                'components': {
                    'payout_ratio_health': payout_health,
                    'consistency_score': round(consistency_score, 1),
                    'growth_health': growth_health,
                    'cut_risk_score': round(cut_risk_score, 1)
                }
            },
            'metrics': {
                'payout_ratio_pct': round(payout_ratio, 2),
                'current_yield_pct': round(current_yield, 2),
                'dividend_growth_rate_pct': round(growth_rate, 2),
                'years_of_data': len(set(d['ex_date'].year for d in dividend_history if hasattr(d['ex_date'], 'year')))
            },
            'recommendation': self._get_recommendation(overall_score, cut_risk_score),
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_portfolio_sustainability(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze sustainability of entire portfolio
        """
        holdings = self.data_extractor.get_portfolio_holdings(user_id)
        
        if not holdings:
            return {
                'success': False,
                'error': 'No portfolio holdings found'
            }
        
        stock_analyses = []
        total_dividend_income = 0
        total_market_value = 0
        
        for holding in holdings:
            ticker = holding['ticker']
            shares = float(holding['shares'])
            market_value = shares * float(holding.get('current_price', 0) or 0)
            annual_income = shares * float(holding.get('annual_dividend', 0) or 0)
            
            analysis = self.analyze_stock_sustainability(ticker)
            
            if analysis['success']:
                stock_analyses.append({
                    'ticker': ticker,
                    'market_value': round(market_value, 2),
                    'annual_income': round(annual_income, 2),
                    'weight_pct': 0,
                    'sustainability_score': analysis['sustainability_analysis']['overall_score'],
                    'grade': analysis['sustainability_analysis']['grade'],
                    'cut_risk_score': analysis['sustainability_analysis']['components']['cut_risk_score']
                })
                
                total_dividend_income += annual_income
                total_market_value += market_value
        
        for stock in stock_analyses:
            stock['weight_pct'] = round(
                (stock['market_value'] / total_market_value * 100) if total_market_value > 0 else 0,
                2
            )
        
        weighted_avg_score = sum(
            s['sustainability_score'] * s['weight_pct'] / 100
            for s in stock_analyses
        ) if stock_analyses else 0
        
        high_risk_stocks = [s for s in stock_analyses if s['cut_risk_score'] > 70]
        
        return {
            'success': True,
            'portfolio_sustainability': {
                'weighted_avg_score': round(weighted_avg_score, 1),
                'overall_grade': self._score_to_grade(weighted_avg_score),
                'total_holdings': len(stock_analyses),
                'high_risk_holdings': len(high_risk_stocks),
                'stocks_by_grade': self._group_by_grade(stock_analyses)
            },
            'stock_analyses': sorted(stock_analyses, key=lambda x: x['sustainability_score'], reverse=True),
            'alerts': self._generate_alerts(stock_analyses),
            'recommendations': self._generate_portfolio_recommendations(stock_analyses),
            'timestamp': datetime.now().isoformat()
        }
    
    def _assess_payout_ratio(self, payout_ratio: float) -> Dict[str, Any]:
        """Assess payout ratio health"""
        if payout_ratio <= 0:
            return {'score': 0, 'status': 'Unknown', 'message': 'No payout ratio data'}
        elif payout_ratio < 30:
            return {'score': 90, 'status': 'Excellent', 'message': 'Very sustainable, room for growth'}
        elif payout_ratio <= 50:
            return {'score': 100, 'status': 'Excellent', 'message': 'Optimal payout ratio'}
        elif payout_ratio <= 70:
            return {'score': 75, 'status': 'Good', 'message': 'Sustainable but limited growth potential'}
        elif payout_ratio <= 90:
            return {'score': 50, 'status': 'Fair', 'message': 'Watch closely for cuts'}
        elif payout_ratio <= 100:
            return {'score': 30, 'status': 'Concerning', 'message': 'High risk of dividend cut'}
        else:
            return {'score': 10, 'status': 'Critical', 'message': 'Unsustainable, cut likely'}
    
    def _calculate_consistency_score(self, dividend_history: List[Dict]) -> float:
        """Calculate dividend payment consistency (0-100)"""
        if len(dividend_history) < 4:
            return 50.0
        
        years_dict = {}
        for div in dividend_history:
            year = div['ex_date'].year if hasattr(div['ex_date'], 'year') else datetime.now().year
            years_dict[year] = years_dict.get(year, 0) + 1
        
        years = sorted(years_dict.keys(), reverse=True)
        recent_years = years[:5] if len(years) >= 5 else years
        
        payments_per_year = [years_dict[y] for y in recent_years]
        
        if len(payments_per_year) < 2:
            return 50.0
        
        avg_payments = statistics.mean(payments_per_year)
        consistency = 100 - (statistics.stdev(payments_per_year) / avg_payments * 100 if avg_payments > 0 else 50)
        
        if len(recent_years) >= 5:
            consistency += 10
        
        return max(min(consistency, 100), 0)
    
    def _calculate_growth_rate(self, dividend_history: List[Dict]) -> float:
        """Calculate dividend growth rate"""
        if len(dividend_history) < 8:
            return 0.0
        
        annual_dividends = {}
        for div in dividend_history:
            year = div['ex_date'].year if hasattr(div['ex_date'], 'year') else datetime.now().year
            annual_dividends[year] = annual_dividends.get(year, 0) + float(div['dividend_amount'] or 0)
        
        years = sorted(annual_dividends.keys())
        if len(years) < 2:
            return 0.0
        
        first_year_div = annual_dividends[years[0]]
        last_year_div = annual_dividends[years[-1]]
        num_years = years[-1] - years[0]
        
        if first_year_div > 0 and num_years > 0:
            cagr = (pow(last_year_div / first_year_div, 1/num_years) - 1) * 100
            return max(min(cagr, 20.0), -10.0)
        
        return 0.0
    
    def _assess_growth_health(self, growth_rate: float) -> Dict[str, Any]:
        """Assess dividend growth health"""
        if growth_rate >= 10:
            return {'score': 100, 'status': 'Excellent', 'message': 'Strong dividend growth'}
        elif growth_rate >= 5:
            return {'score': 85, 'status': 'Very Good', 'message': 'Solid dividend growth'}
        elif growth_rate >= 2:
            return {'score': 70, 'status': 'Good', 'message': 'Modest dividend growth'}
        elif growth_rate >= 0:
            return {'score': 50, 'status': 'Fair', 'message': 'Flat dividends'}
        else:
            return {'score': 20, 'status': 'Poor', 'message': 'Declining dividends'}
    
    def _calculate_cut_risk(
        self,
        payout_ratio: float,
        consistency_score: float,
        growth_rate: float,
        current_yield: float
    ) -> float:
        """Calculate dividend cut risk (0-100, higher = more risk)"""
        risk_score = 50.0
        
        if payout_ratio > 100:
            risk_score += 30
        elif payout_ratio > 90:
            risk_score += 20
        elif payout_ratio > 70:
            risk_score += 10
        elif payout_ratio < 50:
            risk_score -= 15
        
        risk_score -= (consistency_score - 50) * 0.3
        
        if growth_rate < -5:
            risk_score += 20
        elif growth_rate < 0:
            risk_score += 10
        elif growth_rate > 5:
            risk_score -= 10
        
        if current_yield > 10:
            risk_score += 15
        elif current_yield > 7:
            risk_score += 5
        
        return max(min(risk_score, 100), 0)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _get_recommendation(self, overall_score: float, cut_risk: float) -> str:
        """Generate recommendation based on scores"""
        if overall_score >= 85 and cut_risk < 30:
            return 'Strong Buy - Excellent dividend sustainability'
        elif overall_score >= 70 and cut_risk < 50:
            return 'Buy - Good dividend sustainability'
        elif overall_score >= 60 and cut_risk < 60:
            return 'Hold - Moderate sustainability, monitor closely'
        elif cut_risk > 70:
            return 'Sell - High cut risk, consider alternatives'
        else:
            return 'Hold - Average sustainability, watch for changes'
    
    def _group_by_grade(self, stock_analyses: List[Dict]) -> Dict[str, int]:
        """Group stocks by grade"""
        grades = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        for stock in stock_analyses:
            grade = stock.get('grade', 'F')
            grades[grade] = grades.get(grade, 0) + 1
        return grades
    
    def _generate_alerts(self, stock_analyses: List[Dict]) -> List[str]:
        """Generate alerts for portfolio"""
        alerts = []
        
        high_risk = [s for s in stock_analyses if s['cut_risk_score'] > 70]
        if high_risk:
            tickers = ', '.join(s['ticker'] for s in high_risk)
            alerts.append(f"High cut risk detected in {len(high_risk)} stocks: {tickers}")
        
        low_grade = [s for s in stock_analyses if s['grade'] in ['D', 'F']]
        if low_grade:
            tickers = ', '.join(s['ticker'] for s in low_grade)
            alerts.append(f"Low sustainability grades in {len(low_grade)} stocks: {tickers}")
        
        return alerts
    
    def _generate_portfolio_recommendations(self, stock_analyses: List[Dict]) -> List[str]:
        """Generate portfolio-level recommendations"""
        recommendations = []
        
        avg_cut_risk = statistics.mean([s['cut_risk_score'] for s in stock_analyses]) if stock_analyses else 0
        
        if avg_cut_risk > 50:
            recommendations.append("Consider diversifying to lower-risk dividend stocks")
        
        high_risk_weight = sum(
            s['weight_pct'] for s in stock_analyses if s['cut_risk_score'] > 70
        )
        
        if high_risk_weight > 20:
            recommendations.append(f"High-risk stocks represent {high_risk_weight:.1f}% of portfolio - consider rebalancing")
        
        if len(stock_analyses) < 10:
            recommendations.append("Consider adding more positions for better diversification")
        
        return recommendations
