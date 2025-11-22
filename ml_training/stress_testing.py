#!/usr/bin/env python3
"""
Portfolio Stress Testing & Scenario Analysis
Monte Carlo simulations and historical scenario replay
Based on Morningstar Direct's stress testing framework
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    from scipy import stats
    import joblib
except ImportError as e:
    print(f"Error importing required packages: {e}")
    sys.exit(1)


class StressTester:
    """
    Portfolio stress testing and scenario analysis
    Implements Monte Carlo simulations and historical crisis scenarios
    """
    
    def __init__(self, n_simulations: int = 10000):
        """
        Args:
            n_simulations: Number of Monte Carlo simulations to run
        """
        self.n_simulations = n_simulations
        
        # Historical crisis scenarios
        self.crisis_scenarios = {
            'covid_2020': {
                'name': 'COVID-19 Crash (Feb-Mar 2020)',
                'market_shock': -0.34,      # S&P 500 fell 34%
                'duration_days': 33,
                'sector_impacts': {
                    'Technology': -0.20,
                    'Healthcare': -0.15,
                    'Financials': -0.42,
                    'Energy': -0.55,
                    'Consumer Discretionary': -0.30,
                    'Real Estate': -0.35
                }
            },
            'financial_crisis_2008': {
                'name': 'Financial Crisis (Sep 2008 - Mar 2009)',
                'market_shock': -0.57,      # S&P 500 fell 57%
                'duration_days': 180,
                'sector_impacts': {
                    'Financials': -0.78,
                    'Technology': -0.48,
                    'Energy': -0.52,
                    'Consumer Discretionary': -0.60,
                    'Real Estate': -0.68
                }
            },
            'dot_com_2000': {
                'name': 'Dot-com Bubble (Mar 2000 - Oct 2002)',
                'market_shock': -0.49,
                'duration_days': 900,
                'sector_impacts': {
                    'Technology': -0.78,
                    'Telecommunications': -0.72,
                    'Consumer Discretionary': -0.35
                }
            },
            'inflation_shock': {
                'name': 'Inflation Shock Scenario',
                'market_shock': -0.20,
                'duration_days': 120,
                'sector_impacts': {
                    'Technology': -0.30,
                    'Consumer Discretionary': -0.25,
                    'Real Estate': -0.15,
                    'Energy': +0.10,          # Benefits from inflation
                    'Materials': +0.05
                }
            },
            'rate_spike': {
                'name': 'Interest Rate Spike (+300bps)',
                'market_shock': -0.15,
                'duration_days': 90,
                'sector_impacts': {
                    'Utilities': -0.25,
                    'Real Estate': -0.30,
                    'Financials': +0.05,      # Banks benefit
                    'Technology': -0.20
                }
            }
        }
        
    def monte_carlo_simulation(
        self,
        portfolio_weights: np.ndarray,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        horizon_days: int = 252
    ) -> Dict:
        """
        Run Monte Carlo simulations for portfolio
        
        Args:
            portfolio_weights: Current portfolio allocation
            expected_returns: Expected return vector (daily)
            covariance_matrix: Return covariance matrix
            horizon_days: Simulation horizon in trading days
            
        Returns:
            Simulation statistics including VaR, CVaR, and return distribution
        """
        print(f"🎲 Running {self.n_simulations} Monte Carlo simulations over {horizon_days} days...")
        
        n_assets = len(portfolio_weights)
        
        # Generate correlated random returns
        L = np.linalg.cholesky(covariance_matrix)
        
        simulated_portfolio_values = []
        
        for _ in range(self.n_simulations):
            # Generate random returns
            random_returns = np.random.normal(0, 1, (horizon_days, n_assets))
            correlated_returns = expected_returns + random_returns @ L.T
            
            # Calculate portfolio returns
            portfolio_returns = correlated_returns @ portfolio_weights
            
            # Cumulative wealth
            final_value = np.prod(1 + portfolio_returns)
            simulated_portfolio_values.append(final_value)
        
        simulated_portfolio_values = np.array(simulated_portfolio_values)
        
        # Calculate statistics
        mean_final_value = np.mean(simulated_portfolio_values)
        median_final_value = np.median(simulated_portfolio_values)
        std_final_value = np.std(simulated_portfolio_values)
        
        # Value at Risk (VaR)
        var_95 = np.percentile(simulated_portfolio_values, 5)
        var_99 = np.percentile(simulated_portfolio_values, 1)
        
        # Conditional Value at Risk (CVaR / Expected Shortfall)
        cvar_95 = np.mean(simulated_portfolio_values[simulated_portfolio_values <= var_95])
        cvar_99 = np.mean(simulated_portfolio_values[simulated_portfolio_values <= var_99])
        
        # Probability of loss
        prob_loss = np.mean(simulated_portfolio_values < 1.0)
        
        # Maximum drawdown estimate
        max_drawdown = 1.0 - np.min(simulated_portfolio_values)
        
        return {
            'mean_return': float(mean_final_value - 1.0),
            'median_return': float(median_final_value - 1.0),
            'std_dev': float(std_final_value),
            'var_95': float(1.0 - var_95),          # Loss amount
            'var_99': float(1.0 - var_99),
            'cvar_95': float(1.0 - cvar_95),        # Expected loss if in worst 5%
            'cvar_99': float(1.0 - cvar_99),
            'probability_of_loss': float(prob_loss),
            'max_drawdown_estimate': float(max_drawdown),
            'simulations': self.n_simulations,
            'horizon_days': horizon_days
        }
    
    def stress_test_historical_scenarios(
        self,
        portfolio_holdings: List[Dict]
    ) -> Dict:
        """
        Apply historical crisis scenarios to current portfolio
        
        Args:
            portfolio_holdings: List with symbol, weight, sector
            
        Returns:
            Impact of each scenario on portfolio
        """
        print("📉 Stress testing portfolio against historical scenarios...")
        
        df = pd.DataFrame(portfolio_holdings)
        
        scenario_results = {}
        
        for scenario_id, scenario in self.crisis_scenarios.items():
            # Calculate portfolio impact
            portfolio_shock = 0.0
            
            for _, holding in df.iterrows():
                sector = holding.get('sector', 'Unknown')
                weight = holding['weight']
                
                # Get sector-specific impact or use market shock
                sector_impact = scenario['sector_impacts'].get(sector, scenario['market_shock'])
                
                portfolio_shock += weight * sector_impact
            
            # Calculate dividend impact (typically cut 20-40% in crises)
            dividend_shock = 0.3 if scenario_id in ['financial_crisis_2008', 'covid_2020'] else 0.15
            
            scenario_results[scenario_id] = {
                'name': scenario['name'],
                'portfolio_loss': float(portfolio_shock),
                'portfolio_loss_pct': float(portfolio_shock * 100),
                'dividend_cut_estimate': float(dividend_shock),
                'recovery_time_estimate_days': scenario['duration_days'] * 2,  # Rough estimate
                'severity': self._categorize_severity(portfolio_shock)
            }
        
        # Summary statistics
        worst_case = min(scenario_results.values(), key=lambda x: x['portfolio_loss'])
        best_case = max(scenario_results.values(), key=lambda x: x['portfolio_loss'])
        
        return {
            'scenarios': scenario_results,
            'worst_case_scenario': worst_case['name'],
            'worst_case_loss': worst_case['portfolio_loss_pct'],
            'best_case_scenario': best_case['name'],
            'best_case_loss': best_case['portfolio_loss_pct']
        }
    
    def tail_risk_analysis(
        self,
        portfolio_returns: np.ndarray
    ) -> Dict:
        """
        Analyze tail risk characteristics of portfolio
        """
        print("📊 Analyzing tail risk characteristics...")
        
        # Fit distributions to returns
        mean = np.mean(portfolio_returns)
        std = np.std(portfolio_returns)
        
        # Test for normality
        skewness = stats.skew(portfolio_returns)
        kurtosis = stats.kurtosis(portfolio_returns)
        
        # Fit Student's t-distribution for fat tails
        params = stats.t.fit(portfolio_returns)
        df_t, loc_t, scale_t = params
        
        # Downside deviation (semi-variance)
        downside_returns = portfolio_returns[portfolio_returns < mean]
        downside_deviation = np.std(downside_returns) if len(downside_returns) > 0 else 0
        
        # Sortino ratio
        sortino_ratio = (mean - 0) / downside_deviation if downside_deviation > 0 else 0
        
        return {
            'skewness': float(skewness),
            'excess_kurtosis': float(kurtosis),
            'is_fat_tailed': kurtosis > 1.0,
            'is_negatively_skewed': skewness < -0.5,
            't_distribution_df': float(df_t),
            'downside_deviation': float(downside_deviation),
            'sortino_ratio': float(sortino_ratio),
            'tail_risk_rating': self._rate_tail_risk(skewness, kurtosis)
        }
    
    def _categorize_severity(self, loss: float) -> str:
        """Categorize scenario severity"""
        if loss < -0.40:
            return 'catastrophic'
        elif loss < -0.25:
            return 'severe'
        elif loss < -0.15:
            return 'moderate'
        elif loss < -0.05:
            return 'mild'
        else:
            return 'minimal'
    
    def _rate_tail_risk(self, skewness: float, kurtosis: float) -> str:
        """Rate overall tail risk"""
        if kurtosis > 3 and skewness < -1:
            return 'very_high'
        elif kurtosis > 2 or skewness < -0.75:
            return 'high'
        elif kurtosis > 1 or skewness < -0.5:
            return 'moderate'
        else:
            return 'low'
    
    def comprehensive_stress_test(
        self,
        portfolio_data: Dict
    ) -> Dict:
        """
        Run comprehensive stress test suite
        
        Args:
            portfolio_data: Dict with holdings, weights, returns, covariance
        """
        print("🔬 Running comprehensive stress test...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'portfolio_name': portfolio_data.get('name', 'Portfolio')
        }
        
        # Extract data
        weights = np.array(portfolio_data['weights'])
        expected_returns = np.array(portfolio_data.get('expected_returns', [0.0001] * len(weights)))
        cov_matrix = np.array(portfolio_data['covariance_matrix'])
        holdings = portfolio_data['holdings']
        
        # 1. Monte Carlo simulation
        results['monte_carlo'] = self.monte_carlo_simulation(
            weights, expected_returns, cov_matrix
        )
        
        # 2. Historical scenarios
        results['historical_scenarios'] = self.stress_test_historical_scenarios(holdings)
        
        # 3. Tail risk analysis
        if 'historical_returns' in portfolio_data:
            returns = np.array(portfolio_data['historical_returns'])
            results['tail_risk'] = self.tail_risk_analysis(returns)
        
        # 4. Risk summary
        results['risk_summary'] = self._generate_risk_summary(results)
        
        return results
    
    def _generate_risk_summary(self, results: Dict) -> Dict:
        """Generate executive risk summary"""
        mc = results.get('monte_carlo', {})
        scenarios = results.get('historical_scenarios', {})
        
        # Overall risk rating
        var_95 = mc.get('var_95', 0)
        worst_loss = abs(scenarios.get('worst_case_loss', 0)) / 100
        
        max_loss = max(var_95, worst_loss)
        
        if max_loss > 0.40:
            risk_rating = 'high'
        elif max_loss > 0.25:
            risk_rating = 'moderate_high'
        elif max_loss > 0.15:
            risk_rating = 'moderate'
        else:
            risk_rating = 'low_moderate'
        
        return {
            'overall_risk_rating': risk_rating,
            'max_potential_loss': float(max_loss),
            'probability_of_loss': mc.get('probability_of_loss', 0),
            'recommended_actions': self._generate_recommendations(risk_rating, max_loss)
        }
    
    def _generate_recommendations(self, risk_rating: str, max_loss: float) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if risk_rating in ['high', 'moderate_high']:
            recommendations.append("Consider reducing portfolio concentration")
            recommendations.append("Increase allocation to defensive sectors")
            recommendations.append("Consider hedging strategies (puts, inverse ETFs)")
        
        if max_loss > 0.30:
            recommendations.append("High tail risk detected - review position sizes")
            recommendations.append("Consider stop-loss orders for largest positions")
        
        recommendations.append("Maintain cash reserve for buying opportunities during corrections")
        recommendations.append("Rebalance quarterly to maintain target allocations")
        
        return recommendations
    
    def save(self, path: str):
        """Save stress test parameters"""
        model_data = {
            'n_simulations': self.n_simulations,
            'crisis_scenarios': self.crisis_scenarios
        }
        joblib.dump(model_data, path)
        print(f"💾 Stress tester saved to {path}")


def main():
    parser = argparse.ArgumentParser(description='Portfolio Stress Testing')
    parser.add_argument('--data', required=True, help='Path to portfolio data JSON')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--simulations', type=int, default=10000, help='Number of simulations')
    
    args = parser.parse_args()
    
    # Load data
    with open(args.data, 'r') as f:
        portfolio_data = json.load(f)
    
    print(f"📚 Loaded portfolio data")
    
    # Run stress tests
    tester = StressTester(n_simulations=args.simulations)
    results = tester.comprehensive_stress_test(portfolio_data)
    
    # Save
    model_path = os.path.join(args.output, 'stress_tester.joblib')
    tester.save(model_path)
    
    results_path = os.path.join(args.output, 'stress_test_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Stress testing complete!")
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
