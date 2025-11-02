"""
Cash Flow Sensitivity Model
Scenario analysis for portfolio income under various stress conditions
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class CashFlowSensitivityModel:
    """
    Performs stress testing and scenario analysis on portfolio income
    Analyzes "what if" scenarios for dividend cuts, sector downturns, etc.
    """
    
    def __init__(self, data_extractor):
        self.data_extractor = data_extractor
    
    def analyze_cash_flow_sensitivity(
        self,
        holdings: List[Dict[str, Any]],
        scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run multiple stress scenarios on portfolio cash flow
        
        Default scenarios:
        - 10% dividend cut across all holdings
        - 20% dividend cut across all holdings
        - 50% cut in top yielding stock
        - Sector-specific cuts (if concentrated)
        """
        if not holdings:
            return {'success': False, 'error': 'No holdings provided'}
        
        current_annual_income = sum(
            float(h.get('shares', 0)) * float(h.get('annual_dividend', 0) or 0)
            for h in holdings
        )
        
        if scenarios is None:
            scenarios = self._get_default_scenarios(holdings)
        
        scenario_results = []
        for scenario in scenarios:
            result = self._run_scenario(holdings, scenario, current_annual_income)
            scenario_results.append(result)
        
        sector_risk = self._analyze_sector_concentration_risk(holdings)
        
        income_stability_score = self._calculate_income_stability(scenario_results)
        
        return {
            'success': True,
            'baseline': {
                'current_annual_income': round(current_annual_income, 2),
                'current_monthly_income': round(current_annual_income / 12, 2)
            },
            'scenarios': scenario_results,
            'sector_concentration_risk': sector_risk,
            'income_stability_score': round(income_stability_score, 1),
            'risk_assessment': self._assess_overall_risk(scenario_results, sector_risk, income_stability_score),
            'recommendations': self._generate_recommendations(scenario_results, sector_risk),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_default_scenarios(self, holdings: List[Dict]) -> List[Dict[str, Any]]:
        """Generate default stress test scenarios"""
        scenarios = [
            {
                'name': 'Mild Recession (10% cut)',
                'type': 'uniform_cut',
                'cut_percentage': 10,
                'description': 'All dividends reduced by 10%'
            },
            {
                'name': 'Moderate Recession (20% cut)',
                'type': 'uniform_cut',
                'cut_percentage': 20,
                'description': 'All dividends reduced by 20%'
            },
            {
                'name': 'Severe Recession (40% cut)',
                'type': 'uniform_cut',
                'cut_percentage': 40,
                'description': 'All dividends reduced by 40%'
            }
        ]
        
        sorted_by_income = sorted(
            holdings,
            key=lambda x: float(x.get('shares', 0)) * float(x.get('annual_dividend', 0) or 0),
            reverse=True
        )
        
        if sorted_by_income:
            top_ticker = sorted_by_income[0]['ticker']
            scenarios.append({
                'name': f'Top Income Stock Cut ({top_ticker})',
                'type': 'specific_stock',
                'ticker': top_ticker,
                'cut_percentage': 50,
                'description': f'{top_ticker} dividend cut by 50%'
            })
        
        sectors = {}
        for h in holdings:
            sector = h.get('sector', 'Unknown')
            income = float(h.get('shares', 0)) * float(h.get('annual_dividend', 0) or 0)
            sectors[sector] = sectors.get(sector, 0) + income
        
        if sectors:
            top_sector = max(sectors.items(), key=lambda x: x[1])
            if top_sector[1] / sum(sectors.values()) > 0.25:
                scenarios.append({
                    'name': f'{top_sector[0]} Sector Crisis',
                    'type': 'sector_cut',
                    'sector': top_sector[0],
                    'cut_percentage': 30,
                    'description': f'All {top_sector[0]} stocks cut 30%'
                })
        
        return scenarios
    
    def _run_scenario(
        self,
        holdings: List[Dict],
        scenario: Dict[str, Any],
        baseline_income: float
    ) -> Dict[str, Any]:
        """Execute a single stress scenario"""
        scenario_type = scenario['type']
        cut_pct = scenario['cut_percentage']
        
        new_annual_income = 0
        affected_holdings = []
        
        for holding in holdings:
            ticker = holding['ticker']
            shares = float(holding.get('shares', 0))
            annual_div = float(holding.get('annual_dividend', 0) or 0)
            sector = holding.get('sector', 'Unknown')
            
            current_income = shares * annual_div
            
            is_affected = False
            if scenario_type == 'uniform_cut':
                is_affected = True
            elif scenario_type == 'specific_stock' and ticker == scenario.get('ticker'):
                is_affected = True
            elif scenario_type == 'sector_cut' and sector == scenario.get('sector'):
                is_affected = True
            
            if is_affected:
                new_div = annual_div * (1 - cut_pct / 100)
                new_income = shares * new_div
                affected_holdings.append({
                    'ticker': ticker,
                    'original_income': round(current_income, 2),
                    'new_income': round(new_income, 2),
                    'loss': round(current_income - new_income, 2)
                })
            else:
                new_income = current_income
            
            new_annual_income += new_income
        
        income_loss = baseline_income - new_annual_income
        income_loss_pct = (income_loss / baseline_income * 100) if baseline_income > 0 else 0
        
        return {
            'scenario_name': scenario['name'],
            'description': scenario['description'],
            'new_annual_income': round(new_annual_income, 2),
            'new_monthly_income': round(new_annual_income / 12, 2),
            'income_loss': round(income_loss, 2),
            'income_loss_pct': round(income_loss_pct, 2),
            'affected_holdings_count': len(affected_holdings),
            'affected_holdings': affected_holdings,
            'severity': self._categorize_severity(income_loss_pct)
        }
    
    def _analyze_sector_concentration_risk(self, holdings: List[Dict]) -> Dict[str, Any]:
        """Analyze sector concentration and associated risk"""
        sector_income = {}
        total_income = 0
        
        for holding in holdings:
            sector = holding.get('sector', 'Unknown')
            income = float(holding.get('shares', 0)) * float(holding.get('annual_dividend', 0) or 0)
            sector_income[sector] = sector_income.get(sector, 0) + income
            total_income += income
        
        sector_allocation = {
            sector: round((income / total_income * 100), 2) if total_income > 0 else 0
            for sector, income in sector_income.items()
        }
        
        max_concentration = max(sector_allocation.values()) if sector_allocation else 0
        
        risk_level = 'Low'
        if max_concentration > 40:
            risk_level = 'High'
        elif max_concentration > 25:
            risk_level = 'Moderate'
        
        return {
            'sector_allocation': sector_allocation,
            'max_concentration_pct': round(max_concentration, 2),
            'most_concentrated_sector': max(sector_allocation.items(), key=lambda x: x[1])[0] if sector_allocation else None,
            'risk_level': risk_level,
            'diversification_score': round(100 - max_concentration, 1)
        }
    
    def _calculate_income_stability(self, scenario_results: List[Dict]) -> float:
        """
        Calculate income stability score (0-100)
        Based on how well portfolio holds up under stress
        """
        if not scenario_results:
            return 50.0
        
        loss_percentages = [s['income_loss_pct'] for s in scenario_results]
        avg_loss = statistics.mean(loss_percentages)
        max_loss = max(loss_percentages)
        
        stability_score = 100 - (avg_loss * 1.5)
        
        if max_loss > 50:
            stability_score -= 20
        elif max_loss > 30:
            stability_score -= 10
        
        return max(min(stability_score, 100), 0)
    
    def _categorize_severity(self, loss_pct: float) -> str:
        """Categorize scenario severity"""
        if loss_pct < 10:
            return 'Minor'
        elif loss_pct < 20:
            return 'Moderate'
        elif loss_pct < 35:
            return 'Significant'
        else:
            return 'Severe'
    
    def _assess_overall_risk(
        self,
        scenario_results: List[Dict],
        sector_risk: Dict,
        stability_score: float
    ) -> Dict[str, Any]:
        """Provide overall risk assessment"""
        max_loss = max(s['income_loss_pct'] for s in scenario_results) if scenario_results else 0
        
        risk_factors = []
        
        if max_loss > 40:
            risk_factors.append('High vulnerability to severe dividend cuts')
        
        if sector_risk['max_concentration_pct'] > 30:
            risk_factors.append(f"Over-concentrated in {sector_risk['most_concentrated_sector']} sector")
        
        if stability_score < 60:
            risk_factors.append('Low income stability under stress')
        
        overall_risk_level = 'Low'
        if len(risk_factors) >= 2 or max_loss > 35:
            overall_risk_level = 'High'
        elif risk_factors or max_loss > 20:
            overall_risk_level = 'Moderate'
        
        return {
            'risk_level': overall_risk_level,
            'max_potential_loss_pct': round(max_loss, 2),
            'risk_factors': risk_factors,
            'strength': f"Portfolio can maintain {100 - max_loss:.1f}% of income in worst case"
        }
    
    def _generate_recommendations(
        self,
        scenario_results: List[Dict],
        sector_risk: Dict
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        max_loss = max(s['income_loss_pct'] for s in scenario_results) if scenario_results else 0
        
        if max_loss > 30:
            recommendations.append(
                "Consider adding more defensive dividend stocks to reduce sensitivity to cuts"
            )
        
        if sector_risk['max_concentration_pct'] > 30:
            recommendations.append(
                f"Reduce {sector_risk['most_concentrated_sector']} exposure from "
                f"{sector_risk['max_concentration_pct']:.1f}% to below 25% for better diversification"
            )
        
        severe_scenarios = [s for s in scenario_results if s['severity'] in ['Significant', 'Severe']]
        if len(severe_scenarios) > 2:
            recommendations.append(
                "Build cash reserves equal to 6-12 months of dividend income for safety buffer"
            )
        
        if len(sector_risk['sector_allocation']) < 5:
            recommendations.append(
                "Diversify across more sectors to reduce concentration risk"
            )
        
        return recommendations
    
    def analyze_portfolio_sensitivity(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point: Analyze cash flow sensitivity for user's portfolio
        """
        holdings = self.data_extractor.get_portfolio_holdings(user_id)
        
        if not holdings:
            return {
                'success': False,
                'error': 'No portfolio holdings found',
                'message': 'Please add stocks to your portfolio to see sensitivity analysis'
            }
        
        return self.analyze_cash_flow_sensitivity(holdings)
