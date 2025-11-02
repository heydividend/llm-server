"""
Dividend Strategy Analyzer for Harvey
Analyzes advanced dividend investment strategies including timing, margin buying, DRIP, and dividend capture.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger("dividend_strategy")


class DividendStrategy(Enum):
    """Advanced dividend investment strategies"""
    MARGIN_BUYING = "margin_buying"  # Leveraging margin for higher yield
    DRIP = "dividend_reinvestment"  # Automatic dividend reinvestment
    DIVIDEND_CAPTURE = "dividend_capture"  # Buy before ex-date, sell after
    EX_DATE_DIP = "ex_date_dip_buying"  # Buy on ex-dividend price drop
    DECLARATION_PLAY = "declaration_play"  # Buy on declaration, sell after ex-date
    LONG_HOLD = "long_term_hold"  # Traditional buy and hold
    COVERED_CALL = "covered_call_income"  # Write calls against dividend stocks
    PUT_WRITING = "put_writing"  # Write puts to acquire dividend stocks


class DividendStrategyAnalyzer:
    """
    Analyzes optimal dividend investment strategies based on:
    - Dividend dates (declaration, ex-date, record, payment)
    - Historical price patterns around dividend events
    - Tax implications
    - Risk tolerance
    - Capital availability
    """
    
    def __init__(self):
        self.strategies = {}
        self._init_strategy_profiles()
        logger.info("Dividend Strategy Analyzer initialized")
    
    def _init_strategy_profiles(self):
        """Initialize detailed strategy profiles"""
        
        self.strategies = {
            DividendStrategy.MARGIN_BUYING: {
                "name": "Margin Buying for Enhanced Yield",
                "description": "Use margin to amplify dividend income, but increases risk",
                "risk_level": "HIGH",
                "capital_required": "MODERATE",
                "pros": [
                    "Amplifies dividend yield (e.g., 2x leverage = 2x dividends)",
                    "Can increase total return if stock appreciates",
                    "Tax-deductible margin interest (in some jurisdictions)"
                ],
                "cons": [
                    "Margin interest reduces net yield",
                    "Margin calls during market downturns",
                    "Amplifies losses if stock declines",
                    "Not suitable for volatile stocks"
                ],
                "best_for": [
                    "Stable dividend aristocrats",
                    "Low-volatility stocks",
                    "When margin rates < dividend yield"
                ],
                "calculation": "Net Yield = (Dividend Yield × Leverage) - Margin Rate",
                "example": "Buy $20,000 of 4% yielding stock with $10,000 cash + $10,000 margin at 7% = (4% × 2) - 7% = 1% net gain on margin portion"
            },
            
            DividendStrategy.DRIP: {
                "name": "Dividend Reinvestment Plan (DRIP)",
                "description": "Automatically reinvest dividends to compound growth",
                "risk_level": "LOW",
                "capital_required": "LOW",
                "pros": [
                    "Compound growth over time",
                    "Dollar-cost averaging",
                    "Often commission-free",
                    "Some companies offer discount (1-5%)",
                    "Fractional shares possible"
                ],
                "cons": [
                    "No cash income",
                    "Tax owed on reinvested dividends",
                    "Less control over purchase price",
                    "Can't time the market"
                ],
                "best_for": [
                    "Long-term investors",
                    "Retirement accounts (no tax impact)",
                    "Dividend growth stocks",
                    "Young investors building wealth"
                ],
                "calculation": "Future Value = P × (1 + r)^n where r includes dividend reinvestment",
                "example": "100 shares at $50 with 3% yield + 5% growth + DRIP = 500+ shares after 20 years"
            },
            
            DividendStrategy.DIVIDEND_CAPTURE: {
                "name": "Dividend Capture Strategy",
                "description": "Buy before ex-dividend date, sell shortly after for quick income",
                "risk_level": "MEDIUM-HIGH",
                "capital_required": "HIGH",
                "pros": [
                    "Quick income generation",
                    "Can rotate capital frequently",
                    "Predictable dividend dates",
                    "Works in sideways markets"
                ],
                "cons": [
                    "Stock typically drops by dividend amount on ex-date",
                    "Transaction costs can erode profits",
                    "Qualified dividend holding period not met (higher taxes)",
                    "Requires significant capital",
                    "Market risk during holding period"
                ],
                "best_for": [
                    "High-yield stocks with small ex-date drops",
                    "Tax-advantaged accounts",
                    "Experienced traders",
                    "Liquid stocks with tight spreads"
                ],
                "timing": {
                    "buy": "1-3 days before ex-dividend date",
                    "sell": "On ex-date or 1-2 days after",
                    "hold_period": "2-5 trading days"
                },
                "calculation": "Profit = Dividend - Price Drop - Transaction Costs - Taxes",
                "example": "Buy XYZ at $100 for $1 dividend, stock drops to $99.50 on ex-date, sell at $99.60 = $1 dividend + $0.10 loss = $0.90 gross profit"
            },
            
            DividendStrategy.EX_DATE_DIP: {
                "name": "Ex-Dividend Date Dip Buying",
                "description": "Buy on the typical price drop that occurs on ex-dividend date",
                "risk_level": "MEDIUM",
                "capital_required": "MODERATE",
                "pros": [
                    "Buy at predictable discount",
                    "Historical patterns show recovery",
                    "Lower entry price",
                    "Can combine with long-term holding"
                ],
                "cons": [
                    "Miss current dividend",
                    "Drop may exceed dividend amount",
                    "Recovery not guaranteed",
                    "Requires patience for price recovery"
                ],
                "best_for": [
                    "Quality dividend stocks",
                    "Stocks that historically recover quickly",
                    "Long-term investors seeking entry points"
                ],
                "timing": {
                    "buy": "On ex-dividend date at market open",
                    "monitor": "Pre-market for excessive drops",
                    "hold": "Until price recovers (days to weeks)"
                },
                "calculation": "Expected Return = (Recovery % - Transaction Costs) / Days Held × 365",
                "example": "Stock drops $1 on $0.50 dividend, buy at open, recovers $0.75 in 10 days = 27.4% annualized"
            },
            
            DividendStrategy.DECLARATION_PLAY: {
                "name": "Declaration Date Strategy",
                "description": "Buy on dividend declaration, sell after ex-date",
                "risk_level": "MEDIUM",
                "capital_required": "MODERATE",
                "pros": [
                    "Positive momentum after declaration",
                    "Capture both price appreciation and dividend",
                    "Predictable timeline",
                    "Can benefit from dividend increases"
                ],
                "cons": [
                    "Longer holding period (2-6 weeks)",
                    "Market risk exposure",
                    "May miss run-up if buying after declaration",
                    "Dividend may be priced in"
                ],
                "best_for": [
                    "Stocks with dividend increases",
                    "Companies with positive momentum",
                    "Special dividend situations"
                ],
                "timing": {
                    "buy": "On or immediately after declaration date",
                    "hold": "Through ex-dividend date",
                    "sell": "1-3 days after ex-date or on payment date"
                },
                "calculation": "Return = (Price Appreciation + Dividend - Costs) / Capital × (365/Days)",
                "example": "Buy at $50 on declaration, collect $0.50 dividend, sell at $50.75 after 30 days = 30.4% annualized"
            },
            
            DividendStrategy.COVERED_CALL: {
                "name": "Covered Call + Dividend Strategy",
                "description": "Own dividend stocks and sell call options for extra income",
                "risk_level": "MEDIUM-LOW",
                "capital_required": "HIGH",
                "pros": [
                    "Double income stream (dividends + premiums)",
                    "Downside protection from premium",
                    "Works in flat/slightly bullish markets",
                    "Can enhance yield by 10-20% annually"
                ],
                "cons": [
                    "Upside capped at strike price",
                    "Stock can be called away",
                    "Requires 100-share lots",
                    "Options knowledge needed"
                ],
                "best_for": [
                    "Large dividend positions",
                    "Low-volatility dividend stocks",
                    "Income-focused investors",
                    "Sideways markets"
                ],
                "calculation": "Total Yield = Dividend Yield + (Premium × 12) / Stock Price",
                "example": "Own 100 shares at $50 (3% yield), sell monthly $52 calls for $0.50 = 3% + 12% = 15% annual yield"
            },
            
            DividendStrategy.PUT_WRITING: {
                "name": "Cash-Secured Put Writing",
                "description": "Sell puts to potentially acquire dividend stocks at a discount",
                "risk_level": "MEDIUM",
                "capital_required": "HIGH",
                "pros": [
                    "Generate income while waiting to buy",
                    "Acquire stocks at discount to current price",
                    "Premium provides downside cushion",
                    "Can be selective with entry points"
                ],
                "cons": [
                    "May not acquire stock if price rises",
                    "Assigned stock may continue falling",
                    "Cash tied up as collateral",
                    "Miss dividends while waiting"
                ],
                "best_for": [
                    "Investors with cash reserves",
                    "Those wanting specific dividend stocks",
                    "Market corrections/high volatility"
                ],
                "calculation": "Effective Purchase Price = Strike Price - Premium Received",
                "example": "Sell $45 put on $48 stock for $1 premium, if assigned: basis = $44, a 8.3% discount"
            }
        }
    
    def analyze_strategy(
        self,
        symbol: str,
        current_price: float,
        dividend_yield: float,
        ex_date: Optional[datetime] = None,
        declaration_date: Optional[datetime] = None,
        volatility: Optional[float] = None,
        margin_rate: float = 7.0,
        tax_rate: float = 0.15,
        capital_available: float = 10000,
        risk_tolerance: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Analyze optimal dividend strategies for a specific stock.
        
        Args:
            symbol: Stock ticker symbol
            current_price: Current stock price
            dividend_yield: Annual dividend yield percentage
            ex_date: Ex-dividend date
            declaration_date: Declaration date
            volatility: Stock volatility (optional)
            margin_rate: Margin interest rate
            tax_rate: Tax rate on dividends
            capital_available: Available capital
            risk_tolerance: LOW, MEDIUM, HIGH
            
        Returns:
            Strategy recommendations with calculations
        """
        recommendations = {
            "symbol": symbol,
            "current_price": current_price,
            "dividend_yield": dividend_yield,
            "strategies": []
        }
        
        # Calculate quarterly dividend
        quarterly_dividend = (current_price * dividend_yield / 100) / 4
        
        # Analyze each strategy
        for strategy_type, profile in self.strategies.items():
            analysis = {
                "strategy": strategy_type.value,
                "name": profile["name"],
                "risk_level": profile["risk_level"],
                "recommendation": None,
                "calculations": {},
                "score": 0
            }
            
            # Strategy-specific calculations
            if strategy_type == DividendStrategy.MARGIN_BUYING:
                if margin_rate < dividend_yield:
                    leverage = 2.0  # 2x leverage example
                    net_yield = (dividend_yield * leverage) - margin_rate
                    analysis["calculations"] = {
                        "gross_yield_on_margin": dividend_yield * leverage,
                        "margin_cost": margin_rate,
                        "net_yield": net_yield,
                        "annual_income": capital_available * 2 * dividend_yield / 100,
                        "margin_interest": capital_available * margin_rate / 100,
                        "net_income": (capital_available * 2 * dividend_yield / 100) - (capital_available * margin_rate / 100)
                    }
                    analysis["recommendation"] = "FAVORABLE" if net_yield > 0 else "UNFAVORABLE"
                    analysis["score"] = min(net_yield * 10, 100) if net_yield > 0 else 0
                else:
                    analysis["recommendation"] = "UNFAVORABLE"
                    analysis["score"] = 0
            
            elif strategy_type == DividendStrategy.DRIP:
                # DRIP is almost always favorable for long-term investors
                years = 10
                shares = capital_available / current_price
                future_shares = shares * ((1 + dividend_yield/100) ** years)
                analysis["calculations"] = {
                    "initial_shares": shares,
                    "shares_after_10_years": future_shares,
                    "value_after_10_years": future_shares * current_price * 1.5,  # Assume 50% price appreciation
                    "total_return": ((future_shares * current_price * 1.5) / capital_available - 1) * 100
                }
                analysis["recommendation"] = "HIGHLY_FAVORABLE"
                analysis["score"] = 85
            
            elif strategy_type == DividendStrategy.DIVIDEND_CAPTURE:
                if volatility and volatility < 20:  # Low volatility preferred
                    expected_drop = quarterly_dividend * 0.85  # Stock typically drops 85% of dividend
                    transaction_cost = current_price * 0.002  # 0.2% round trip
                    tax_impact = quarterly_dividend * (0.37 - tax_rate)  # Ordinary vs qualified
                    
                    net_profit = quarterly_dividend - expected_drop - transaction_cost - tax_impact
                    analysis["calculations"] = {
                        "dividend_captured": quarterly_dividend,
                        "expected_price_drop": expected_drop,
                        "transaction_costs": transaction_cost,
                        "additional_tax": tax_impact,
                        "net_profit_per_share": net_profit,
                        "return_on_capital": (net_profit / current_price) * 100,
                        "annualized_return": (net_profit / current_price) * 365 / 5 * 100  # 5-day hold
                    }
                    analysis["recommendation"] = "FAVORABLE" if net_profit > 0 else "UNFAVORABLE"
                    analysis["score"] = max(min((net_profit / current_price) * 1000, 100), 0)
                else:
                    analysis["recommendation"] = "RISKY"
                    analysis["score"] = 30
            
            elif strategy_type == DividendStrategy.EX_DATE_DIP:
                typical_recovery_days = 7
                expected_dip = quarterly_dividend * 1.2  # Often dips more than dividend
                recovery_potential = quarterly_dividend * 0.7  # Recovers 70% of excess dip
                
                analysis["calculations"] = {
                    "expected_dip": expected_dip,
                    "buy_price": current_price - expected_dip,
                    "recovery_target": current_price - (expected_dip - recovery_potential),
                    "profit_potential": recovery_potential,
                    "return_if_successful": (recovery_potential / (current_price - expected_dip)) * 100,
                    "annualized_return": (recovery_potential / (current_price - expected_dip)) * 365 / typical_recovery_days * 100
                }
                analysis["recommendation"] = "FAVORABLE"
                analysis["score"] = 65
            
            elif strategy_type == DividendStrategy.DECLARATION_PLAY:
                if declaration_date and ex_date:
                    days_between = (ex_date - declaration_date).days
                    historical_appreciation = dividend_yield / 100 * 0.3  # 30% of yield as price appreciation
                    
                    analysis["calculations"] = {
                        "holding_period_days": days_between,
                        "expected_appreciation": historical_appreciation * current_price,
                        "dividend_income": quarterly_dividend,
                        "total_return": quarterly_dividend + (historical_appreciation * current_price),
                        "return_percentage": ((quarterly_dividend + (historical_appreciation * current_price)) / current_price) * 100,
                        "annualized_return": ((quarterly_dividend + (historical_appreciation * current_price)) / current_price) * 365 / max(days_between, 1) * 100
                    }
                    analysis["recommendation"] = "FAVORABLE"
                    analysis["score"] = 70
            
            elif strategy_type == DividendStrategy.COVERED_CALL:
                monthly_premium = current_price * 0.01  # 1% monthly premium estimate
                annual_premium = monthly_premium * 12
                total_yield = dividend_yield + (annual_premium / current_price * 100)
                
                analysis["calculations"] = {
                    "monthly_premium": monthly_premium,
                    "annual_premium_income": annual_premium,
                    "dividend_income": capital_available * dividend_yield / 100,
                    "total_income": annual_premium + (capital_available * dividend_yield / 100),
                    "enhanced_yield": total_yield,
                    "yield_improvement": total_yield - dividend_yield
                }
                analysis["recommendation"] = "FAVORABLE" if total_yield > 10 else "MODERATE"
                analysis["score"] = min(total_yield * 5, 100)
            
            elif strategy_type == DividendStrategy.PUT_WRITING:
                put_premium = current_price * 0.02  # 2% premium for ATM put
                strike_discount = current_price * 0.05  # 5% OTM
                effective_purchase = current_price * 0.95 - put_premium
                
                analysis["calculations"] = {
                    "put_premium": put_premium,
                    "strike_price": current_price * 0.95,
                    "effective_purchase_price": effective_purchase,
                    "discount_to_current": ((current_price - effective_purchase) / current_price) * 100,
                    "premium_yield": (put_premium / (current_price * 0.95)) * 12 * 100,  # Annualized
                    "break_even": effective_purchase
                }
                analysis["recommendation"] = "FAVORABLE"
                analysis["score"] = 60
            
            recommendations["strategies"].append(analysis)
        
        # Sort strategies by score
        recommendations["strategies"] = sorted(
            recommendations["strategies"],
            key=lambda x: x["score"],
            reverse=True
        )
        
        # Add risk-adjusted recommendations
        recommendations["risk_adjusted_recommendation"] = self._get_risk_adjusted_recommendation(
            recommendations["strategies"],
            risk_tolerance
        )
        
        return recommendations
    
    def _get_risk_adjusted_recommendation(
        self,
        strategies: List[Dict],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Get best strategy based on risk tolerance"""
        
        risk_map = {
            "LOW": ["DRIP", "dividend_reinvestment", "covered_call_income"],
            "MEDIUM": ["ex_date_dip_buying", "declaration_play", "put_writing"],
            "HIGH": ["margin_buying", "dividend_capture"]
        }
        
        allowed_strategies = risk_map.get(risk_tolerance, risk_map["MEDIUM"])
        
        # Filter strategies by risk tolerance
        suitable = [s for s in strategies if s["strategy"] in allowed_strategies and s["score"] > 30]
        
        if suitable:
            best = suitable[0]
            return {
                "recommended_strategy": best["name"],
                "reason": f"Best {risk_tolerance}-risk strategy with score {best['score']:.1f}",
                "expected_return": best.get("calculations", {}).get("annualized_return", "N/A"),
                "implementation": self.strategies[DividendStrategy(best["strategy"])].get("timing", {})
            }
        else:
            return {
                "recommended_strategy": "DRIP",
                "reason": f"Default safe strategy for {risk_tolerance} risk tolerance",
                "expected_return": f"{dividend_yield}% + growth",
                "implementation": {"action": "Enable DRIP with broker"}
            }
    
    def get_calendar_strategy(
        self,
        symbol: str,
        declaration_date: datetime,
        ex_date: datetime,
        record_date: datetime,
        payment_date: datetime,
        current_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Provide date-specific strategy recommendations based on dividend calendar.
        
        Returns optimal actions for each date in the dividend cycle.
        """
        if not current_date:
            current_date = datetime.now()
        
        calendar_strategy = {
            "symbol": symbol,
            "current_date": current_date.strftime("%Y-%m-%d"),
            "dividend_dates": {
                "declaration": declaration_date.strftime("%Y-%m-%d"),
                "ex_dividend": ex_date.strftime("%Y-%m-%d"),
                "record": record_date.strftime("%Y-%m-%d"),
                "payment": payment_date.strftime("%Y-%m-%d")
            },
            "timeline_strategies": []
        }
        
        # Days until each date
        days_to_declaration = (declaration_date - current_date).days
        days_to_ex = (ex_date - current_date).days
        days_to_record = (record_date - current_date).days
        days_to_payment = (payment_date - current_date).days
        
        # Pre-declaration strategy
        if days_to_declaration > 0:
            calendar_strategy["timeline_strategies"].append({
                "period": "Pre-Declaration",
                "days_until": days_to_declaration,
                "strategies": [
                    {
                        "action": "Accumulate shares",
                        "reason": "Build position before potential dividend increase announcement",
                        "risk": "LOW"
                    },
                    {
                        "action": "Sell cash-secured puts",
                        "reason": "Collect premium while waiting to acquire shares",
                        "risk": "MEDIUM"
                    }
                ]
            })
        
        # Declaration to ex-date strategy
        if days_to_declaration <= 0 < days_to_ex:
            calendar_strategy["timeline_strategies"].append({
                "period": "Post-Declaration",
                "days_until_ex": days_to_ex,
                "strategies": [
                    {
                        "action": "Declaration Play - Buy now",
                        "reason": "Capture dividend and potential appreciation",
                        "risk": "MEDIUM"
                    },
                    {
                        "action": "Dividend Capture - Buy 1-2 days before ex-date",
                        "reason": "Minimize holding period for quick income",
                        "risk": "HIGH"
                    }
                ]
            })
        
        # Ex-date strategy
        if days_to_ex == 0:
            calendar_strategy["timeline_strategies"].append({
                "period": "Ex-Dividend Date",
                "days_until": 0,
                "strategies": [
                    {
                        "action": "Ex-Date Dip Buy",
                        "reason": "Buy on typical morning dip for discount entry",
                        "risk": "MEDIUM"
                    },
                    {
                        "action": "Sell if dividend captured",
                        "reason": "Complete dividend capture strategy",
                        "risk": "MEDIUM"
                    }
                ]
            })
        
        # Post ex-date strategy
        if 0 < days_to_ex < -5:
            calendar_strategy["timeline_strategies"].append({
                "period": "Post Ex-Date",
                "days_since_ex": -days_to_ex,
                "strategies": [
                    {
                        "action": "Hold for recovery",
                        "reason": "Wait for typical price recovery post-ex-date",
                        "risk": "LOW"
                    },
                    {
                        "action": "Sell covered calls",
                        "reason": "Generate income while holding",
                        "risk": "MEDIUM"
                    }
                ]
            })
        
        # Recommend current action
        if days_to_ex > 10:
            calendar_strategy["recommended_action"] = "Consider accumulating shares or selling puts"
        elif 2 < days_to_ex <= 10:
            calendar_strategy["recommended_action"] = "Prepare for dividend capture or declaration play"
        elif 0 < days_to_ex <= 2:
            calendar_strategy["recommended_action"] = "Execute dividend capture if desired"
        elif days_to_ex == 0:
            calendar_strategy["recommended_action"] = "Monitor for ex-date dip buying opportunity"
        else:
            calendar_strategy["recommended_action"] = "Hold for recovery or sell covered calls"
        
        return calendar_strategy


# Global instance
dividend_strategy = DividendStrategyAnalyzer()