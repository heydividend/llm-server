"""
4-Tier Dividend Analytics Framework for Harvey
Provides Descriptive, Diagnostic, Predictive, and Prescriptive analytics for dividend analysis.
"""

import datetime as dt
from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
import statistics
import logging

logger = logging.getLogger("dividend_analytics")


def analyze_payment_history(distributions: List[Dict]) -> Dict[str, Any]:
    """
    Descriptive Analytics: Analyze payment patterns, frequency, and consistency.
    
    Args:
        distributions: List of distribution records with amount and date fields
        
    Returns:
        Dict containing:
            - total_payments: Number of payments
            - frequency: Payment frequency (monthly, quarterly, annual)
            - avg_amount: Average payment amount
            - consistency_score: 0-100 score (higher = more consistent)
            - pattern: Payment pattern description
    """
    if not distributions:
        return {
            "total_payments": 0,
            "frequency": "N/A",
            "avg_amount": 0.0,
            "consistency_score": 0,
            "pattern": "No payment history available"
        }
    
    try:
        amounts = []
        dates = []
        
        for dist in distributions:
            amount = dist.get('Dividend_Amount') or dist.get('AdjDividend_Amount') or dist.get('Distribution_Amount')
            date = dist.get('Payment_Date') or dist.get('Ex_Dividend_Date') or dist.get('Ex_Date')
            
            if amount is not None and date is not None:
                amounts.append(float(amount))
                if isinstance(date, str):
                    date = dt.datetime.fromisoformat(date.replace('Z', '+00:00')).date()
                elif isinstance(date, dt.datetime):
                    date = date.date()
                dates.append(date)
        
        if not amounts or not dates:
            return {
                "total_payments": len(distributions),
                "frequency": "N/A",
                "avg_amount": 0.0,
                "consistency_score": 0,
                "pattern": "Insufficient data"
            }
        
        total_payments = len(amounts)
        avg_amount = statistics.mean(amounts)
        
        frequency = _detect_frequency(dates)
        
        variance = statistics.variance(amounts) if len(amounts) > 1 else 0
        cv = (variance ** 0.5) / avg_amount if avg_amount > 0 else 1.0
        consistency_score = max(0, min(100, int((1 - min(cv, 1.0)) * 100)))
        
        if total_payments >= 12:
            pattern = f"{total_payments} consecutive payments"
        elif total_payments >= 4:
            pattern = f"{total_payments} payments tracked"
        else:
            pattern = f"Limited payment history ({total_payments} payments)"
        
        return {
            "total_payments": total_payments,
            "frequency": frequency,
            "avg_amount": round(avg_amount, 4),
            "consistency_score": consistency_score,
            "pattern": pattern
        }
    
    except Exception as e:
        logger.error(f"Error analyzing payment history: {e}")
        return {
            "total_payments": 0,
            "frequency": "N/A",
            "avg_amount": 0.0,
            "consistency_score": 0,
            "pattern": "Analysis error"
        }


def calculate_yield_trends(ticker: str, distributions: List[Dict], prices: List[Dict]) -> Dict[str, Any]:
    """
    Descriptive Analytics: Calculate yield trends over time.
    
    Args:
        ticker: Ticker symbol
        distributions: Distribution history
        prices: Price history
        
    Returns:
        Dict containing:
            - current_yield: Current dividend yield (annualized)
            - avg_yield: Average yield over period
            - yield_trend: "increasing", "decreasing", "stable"
            - yield_change_pct: Percentage change in yield
    """
    if not distributions or not prices:
        return {
            "current_yield": "N/A",
            "avg_yield": "N/A",
            "yield_trend": "N/A",
            "yield_change_pct": "N/A"
        }
    
    try:
        latest_price = float(prices[0].get('Price', 0)) if prices else 0
        
        if latest_price <= 0:
            return {
                "current_yield": "N/A",
                "avg_yield": "N/A",
                "yield_trend": "N/A",
                "yield_change_pct": "N/A"
            }
        
        recent_distributions = distributions[:12] if len(distributions) >= 12 else distributions
        annual_distribution = sum(
            float(d.get('Dividend_Amount') or d.get('Distribution_Amount') or 0)
            for d in recent_distributions
        )
        
        current_yield = (annual_distribution / latest_price) * 100
        
        if len(distributions) >= 24:
            older_distributions = distributions[12:24]
            older_annual = sum(
                float(d.get('Dividend_Amount') or d.get('Distribution_Amount') or 0)
                for d in older_distributions
            )
            
            older_price_avg = statistics.mean([float(p.get('Price', 0)) for p in prices[12:24]]) if len(prices) >= 24 else latest_price
            
            if older_price_avg > 0:
                older_yield = (older_annual / older_price_avg) * 100
                avg_yield = (current_yield + older_yield) / 2
                yield_change_pct = ((current_yield - older_yield) / older_yield) * 100 if older_yield > 0 else 0
                
                if abs(yield_change_pct) < 5:
                    yield_trend = "stable"
                elif yield_change_pct > 0:
                    yield_trend = "increasing"
                else:
                    yield_trend = "decreasing"
            else:
                avg_yield = current_yield
                yield_change_pct = 0
                yield_trend = "stable"
        else:
            avg_yield = current_yield
            yield_change_pct = 0
            yield_trend = "stable"
        
        return {
            "current_yield": round(current_yield, 2),
            "avg_yield": round(avg_yield, 2),
            "yield_trend": yield_trend,
            "yield_change_pct": round(yield_change_pct, 2)
        }
    
    except Exception as e:
        logger.error(f"Error calculating yield trends for {ticker}: {e}")
        return {
            "current_yield": "N/A",
            "avg_yield": "N/A",
            "yield_trend": "N/A",
            "yield_change_pct": "N/A"
        }


def analyze_distribution_consistency(distributions: List[Dict]) -> Dict[str, Any]:
    """
    Descriptive Analytics: Analyze payment regularity, variance, and outliers.
    
    Args:
        distributions: Distribution history
        
    Returns:
        Dict containing:
            - regularity_score: 0-100 score
            - variance: Payment variance
            - outliers: Number of outlier payments
            - missed_payments: Estimated missed payments
    """
    if not distributions or len(distributions) < 3:
        return {
            "regularity_score": 0,
            "variance": "N/A",
            "outliers": 0,
            "missed_payments": 0
        }
    
    try:
        amounts = [
            float(d.get('Dividend_Amount') or d.get('Distribution_Amount') or 0)
            for d in distributions
            if (d.get('Dividend_Amount') or d.get('Distribution_Amount'))
        ]
        
        if not amounts:
            return {
                "regularity_score": 0,
                "variance": "N/A",
                "outliers": 0,
                "missed_payments": 0
            }
        
        mean_amount = statistics.mean(amounts)
        variance = statistics.variance(amounts) if len(amounts) > 1 else 0
        std_dev = variance ** 0.5
        
        outliers = sum(1 for a in amounts if abs(a - mean_amount) > 2 * std_dev)
        
        dates = []
        for d in distributions:
            date = d.get('Payment_Date') or d.get('Ex_Dividend_Date') or d.get('Ex_Date')
            if date:
                if isinstance(date, str):
                    date = dt.datetime.fromisoformat(date.replace('Z', '+00:00')).date()
                elif isinstance(date, dt.datetime):
                    date = date.date()
                dates.append(date)
        
        missed_payments = 0
        if len(dates) >= 2:
            dates_sorted = sorted(dates)
            intervals = [(dates_sorted[i+1] - dates_sorted[i]).days for i in range(len(dates_sorted)-1)]
            
            if intervals:
                avg_interval = statistics.mean(intervals)
                
                for interval in intervals:
                    if interval > avg_interval * 1.8:
                        missed_payments += 1
        
        cv = (std_dev / mean_amount) if mean_amount > 0 else 1.0
        regularity_score = max(0, min(100, int((1 - min(cv, 1.0)) * 100)))
        
        if missed_payments > 0:
            regularity_score = max(0, regularity_score - (missed_payments * 10))
        
        return {
            "regularity_score": regularity_score,
            "variance": round(variance, 6),
            "outliers": outliers,
            "missed_payments": missed_payments
        }
    
    except Exception as e:
        logger.error(f"Error analyzing distribution consistency: {e}")
        return {
            "regularity_score": 0,
            "variance": "N/A",
            "outliers": 0,
            "missed_payments": 0
        }


def summarize_historical_performance(ticker: str, distributions: List[Dict], period: str = "5Y") -> Dict[str, Any]:
    """
    Descriptive Analytics: Comprehensive historical summary.
    
    Args:
        ticker: Ticker symbol
        distributions: Distribution history
        period: Time period (e.g., "5Y", "3Y", "1Y")
        
    Returns:
        Comprehensive performance summary dict
    """
    if not distributions:
        return {
            "ticker": ticker,
            "period": period,
            "summary": "No historical data available"
        }
    
    try:
        payment_analysis = analyze_payment_history(distributions)
        consistency_analysis = analyze_distribution_consistency(distributions)
        
        total_distributed = sum(
            float(d.get('Dividend_Amount') or d.get('Distribution_Amount') or 0)
            for d in distributions
        )
        
        summary = {
            "ticker": ticker,
            "period": period,
            "total_payments": payment_analysis["total_payments"],
            "total_distributed": round(total_distributed, 2),
            "avg_payment": payment_analysis["avg_amount"],
            "frequency": payment_analysis["frequency"],
            "consistency_score": payment_analysis["consistency_score"],
            "regularity_score": consistency_analysis["regularity_score"],
            "summary": f"{ticker} has paid {payment_analysis['total_payments']} distributions with {payment_analysis['consistency_score']}% consistency"
        }
        
        return summary
    
    except Exception as e:
        logger.error(f"Error summarizing historical performance for {ticker}: {e}")
        return {
            "ticker": ticker,
            "period": period,
            "summary": "Analysis error"
        }


def diagnose_dividend_cut(ticker: str, old_amount: float, new_amount: float, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Diagnostic Analytics: Analyze why dividend was cut.
    
    Args:
        ticker: Ticker symbol
        old_amount: Previous dividend amount
        new_amount: New dividend amount
        context: Optional context (earnings, cash flow data)
        
    Returns:
        Diagnosis dict with likely causes
    """
    cut_pct = ((new_amount - old_amount) / old_amount) * 100 if old_amount > 0 else 0
    
    severity = "minor" if abs(cut_pct) < 10 else "moderate" if abs(cut_pct) < 25 else "severe"
    
    likely_causes = []
    
    if cut_pct < -40:
        likely_causes.append("Significant financial distress or earnings decline")
    elif cut_pct < -20:
        likely_causes.append("Cash flow constraints or reduced profitability")
    elif cut_pct < -10:
        likely_causes.append("Conservative payout adjustment or seasonal variation")
    
    if ticker.endswith(('Y', 'LY', 'X')):
        likely_causes.append("Covered call premium volatility (common in YieldMax/similar ETFs)")
    
    return {
        "ticker": ticker,
        "old_amount": old_amount,
        "new_amount": new_amount,
        "cut_percentage": round(cut_pct, 2),
        "severity": severity,
        "likely_causes": likely_causes if likely_causes else ["Normal dividend fluctuation"],
        "explanation": f"Dividend {'cut' if cut_pct < 0 else 'increased'} by {abs(cut_pct):.1f}% ({severity} change)"
    }


def diagnose_yield_change(ticker: str, yield_change_pct: float, price_change_pct: Optional[float] = None, distribution_change_pct: Optional[float] = None) -> Dict[str, Any]:
    """
    Diagnostic Analytics: Explain if yield change is due to price movement or distribution change.
    
    Args:
        ticker: Ticker symbol
        yield_change_pct: Percentage change in yield
        price_change_pct: Optional price change percentage
        distribution_change_pct: Optional distribution change percentage
        
    Returns:
        Diagnosis dict explaining yield change drivers
    """
    primary_driver = "unknown"
    explanation = ""
    
    if price_change_pct is not None and distribution_change_pct is not None:
        if abs(price_change_pct) > abs(distribution_change_pct) * 2:
            primary_driver = "price_movement"
            explanation = f"Yield change primarily driven by {abs(price_change_pct):.1f}% price {'increase' if price_change_pct > 0 else 'decrease'}"
        elif abs(distribution_change_pct) > abs(price_change_pct) * 2:
            primary_driver = "distribution_change"
            explanation = f"Yield change primarily driven by {abs(distribution_change_pct):.1f}% distribution {'increase' if distribution_change_pct > 0 else 'decrease'}"
        else:
            primary_driver = "combined"
            explanation = f"Yield change driven by both price ({price_change_pct:+.1f}%) and distribution ({distribution_change_pct:+.1f}%) changes"
    else:
        explanation = f"Yield changed by {yield_change_pct:+.1f}% - additional data needed for root cause analysis"
    
    return {
        "ticker": ticker,
        "yield_change_pct": round(yield_change_pct, 2),
        "primary_driver": primary_driver,
        "price_change_pct": price_change_pct,
        "distribution_change_pct": distribution_change_pct,
        "explanation": explanation
    }


def diagnose_payment_irregularity(distributions: List[Dict]) -> Dict[str, Any]:
    """
    Diagnostic Analytics: Identify special dividends, missed payments, pattern breaks.
    
    Args:
        distributions: Distribution history
        
    Returns:
        Irregularity diagnosis dict
    """
    if not distributions or len(distributions) < 3:
        return {
            "has_irregularities": False,
            "special_dividends": 0,
            "missed_payments": 0,
            "pattern_breaks": [],
            "diagnosis": "Insufficient data for irregularity analysis"
        }
    
    try:
        amounts = [
            float(d.get('Dividend_Amount') or d.get('Distribution_Amount') or 0)
            for d in distributions
            if (d.get('Dividend_Amount') or d.get('Distribution_Amount'))
        ]
        
        mean_amount = statistics.mean(amounts)
        std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        special_dividends = sum(1 for a in amounts if a > mean_amount + 2 * std_dev)
        
        consistency = analyze_distribution_consistency(distributions)
        missed_payments = consistency.get("missed_payments", 0)
        
        pattern_breaks = []
        if len(amounts) >= 4:
            for i in range(1, len(amounts)):
                change_pct = ((amounts[i] - amounts[i-1]) / amounts[i-1]) * 100 if amounts[i-1] > 0 else 0
                if abs(change_pct) > 30:
                    pattern_breaks.append({
                        "position": i,
                        "change_pct": round(change_pct, 2),
                        "type": "increase" if change_pct > 0 else "decrease"
                    })
        
        has_irregularities = special_dividends > 0 or missed_payments > 0 or len(pattern_breaks) > 0
        
        diagnosis_parts = []
        if special_dividends > 0:
            diagnosis_parts.append(f"{special_dividends} special dividend(s) detected")
        if missed_payments > 0:
            diagnosis_parts.append(f"{missed_payments} likely missed payment(s)")
        if pattern_breaks:
            diagnosis_parts.append(f"{len(pattern_breaks)} significant pattern break(s)")
        
        diagnosis = "; ".join(diagnosis_parts) if diagnosis_parts else "No significant irregularities detected"
        
        return {
            "has_irregularities": has_irregularities,
            "special_dividends": special_dividends,
            "missed_payments": missed_payments,
            "pattern_breaks": pattern_breaks,
            "diagnosis": diagnosis
        }
    
    except Exception as e:
        logger.error(f"Error diagnosing payment irregularity: {e}")
        return {
            "has_irregularities": False,
            "special_dividends": 0,
            "missed_payments": 0,
            "pattern_breaks": [],
            "diagnosis": "Analysis error"
        }


def explain_distribution_variance(distributions: List[Dict], ticker: str = "") -> Dict[str, Any]:
    """
    Diagnostic Analytics: Explain why distributions fluctuate.
    
    Args:
        distributions: Distribution history
        ticker: Ticker symbol
        
    Returns:
        Explanation dict for variance
    """
    if not distributions or len(distributions) < 3:
        return {
            "variance_level": "N/A",
            "explanation": "Insufficient data to analyze variance",
            "likely_reasons": []
        }
    
    try:
        consistency = analyze_distribution_consistency(distributions)
        variance = consistency.get("variance", 0)
        
        if variance == "N/A" or variance == 0:
            return {
                "variance_level": "none",
                "explanation": "Distributions are highly consistent",
                "likely_reasons": ["Fixed distribution policy"]
            }
        
        amounts = [
            float(d.get('Dividend_Amount') or d.get('Distribution_Amount') or 0)
            for d in distributions
            if (d.get('Dividend_Amount') or d.get('Distribution_Amount'))
        ]
        
        mean_amount = statistics.mean(amounts)
        cv = (variance ** 0.5) / mean_amount if mean_amount > 0 else 0
        
        if cv < 0.05:
            variance_level = "low"
        elif cv < 0.15:
            variance_level = "moderate"
        else:
            variance_level = "high"
        
        likely_reasons = []
        
        if ticker.endswith(('Y', 'LY', 'X')):
            likely_reasons.append("Covered call strategy - distributions vary with option premium income")
        
        if variance_level == "high":
            likely_reasons.append("Variable income structure (REITs, MLPs, or option-income funds)")
            likely_reasons.append("NAV-based distributions fluctuating with portfolio performance")
        elif variance_level == "moderate":
            likely_reasons.append("Seasonal business patterns affecting cash flows")
            likely_reasons.append("Opportunistic special dividends")
        else:
            likely_reasons.append("Stable dividend policy with minimal variance")
        
        explanation = f"{variance_level.capitalize()} variance detected (CV: {cv:.2%})"
        
        return {
            "variance_level": variance_level,
            "coefficient_of_variation": round(cv, 4),
            "explanation": explanation,
            "likely_reasons": likely_reasons
        }
    
    except Exception as e:
        logger.error(f"Error explaining distribution variance: {e}")
        return {
            "variance_level": "N/A",
            "explanation": "Analysis error",
            "likely_reasons": []
        }


def predict_next_distribution(ticker: str, distributions: List[Dict]) -> Dict[str, Any]:
    """
    Predictive Analytics: Forecast next payment amount and date.
    
    Args:
        ticker: Ticker symbol
        distributions: Distribution history
        
    Returns:
        Prediction dict with next payment forecast
    """
    if not distributions or len(distributions) < 2:
        return {
            "ticker": ticker,
            "predicted_amount": "N/A",
            "predicted_date": "N/A",
            "confidence": "low",
            "basis": "Insufficient historical data"
        }
    
    try:
        recent_amounts = [
            float(d.get('Dividend_Amount') or d.get('Distribution_Amount') or 0)
            for d in distributions[:3]
            if (d.get('Dividend_Amount') or d.get('Distribution_Amount'))
        ]
        
        recent_dates = []
        for d in distributions[:3]:
            date = d.get('Payment_Date') or d.get('Ex_Dividend_Date') or d.get('Ex_Date')
            if date:
                if isinstance(date, str):
                    date = dt.datetime.fromisoformat(date.replace('Z', '+00:00')).date()
                elif isinstance(date, dt.datetime):
                    date = date.date()
                recent_dates.append(date)
        
        if not recent_amounts or not recent_dates:
            return {
                "ticker": ticker,
                "predicted_amount": "N/A",
                "predicted_date": "N/A",
                "confidence": "low",
                "basis": "Incomplete data"
            }
        
        predicted_amount = statistics.mean(recent_amounts)
        
        if len(recent_dates) >= 2:
            recent_dates_sorted = sorted(recent_dates, reverse=True)
            interval = (recent_dates_sorted[0] - recent_dates_sorted[1]).days
            predicted_date = recent_dates_sorted[0] + dt.timedelta(days=interval)
        else:
            predicted_date = recent_dates[0] + dt.timedelta(days=30)
        
        variance = statistics.variance(recent_amounts) if len(recent_amounts) > 1 else 0
        cv = (variance ** 0.5) / predicted_amount if predicted_amount > 0 else 1.0
        
        if cv < 0.1:
            confidence = "high"
        elif cv < 0.25:
            confidence = "medium"
        else:
            confidence = "low"
        
        basis = f"Based on {len(recent_amounts)} recent payments averaging ${predicted_amount:.4f}"
        
        return {
            "ticker": ticker,
            "predicted_amount": round(predicted_amount, 4),
            "predicted_date": predicted_date.isoformat(),
            "confidence": confidence,
            "basis": basis
        }
    
    except Exception as e:
        logger.error(f"Error predicting next distribution for {ticker}: {e}")
        return {
            "ticker": ticker,
            "predicted_amount": "N/A",
            "predicted_date": "N/A",
            "confidence": "low",
            "basis": "Prediction error"
        }


def predict_annual_income(ticker: str, shares: int, distributions: List[Dict]) -> Dict[str, Any]:
    """
    Predictive Analytics: Project annual dividend income.
    
    Args:
        ticker: Ticker symbol
        shares: Number of shares owned
        distributions: Distribution history
        
    Returns:
        Annual income projection dict
    """
    if not distributions:
        return {
            "ticker": ticker,
            "shares": shares,
            "projected_annual_income": 0,
            "monthly_average": 0,
            "basis": "No distribution history"
        }
    
    try:
        recent_12_months = distributions[:12] if len(distributions) >= 12 else distributions
        
        total_annual = sum(
            float(d.get('Dividend_Amount') or d.get('Distribution_Amount') or 0)
            for d in recent_12_months
        )
        
        if len(distributions) < 12:
            months_of_data = len(distributions)
            total_annual = (total_annual / months_of_data) * 12 if months_of_data > 0 else 0
            basis = f"Annualized from {months_of_data} months of data"
        else:
            basis = "Based on trailing 12-month distributions"
        
        projected_annual_income = shares * total_annual
        monthly_average = projected_annual_income / 12
        
        return {
            "ticker": ticker,
            "shares": shares,
            "projected_annual_income": round(projected_annual_income, 2),
            "monthly_average": round(monthly_average, 2),
            "per_share_annual": round(total_annual, 4),
            "basis": basis
        }
    
    except Exception as e:
        logger.error(f"Error predicting annual income for {ticker}: {e}")
        return {
            "ticker": ticker,
            "shares": shares,
            "projected_annual_income": 0,
            "monthly_average": 0,
            "basis": "Calculation error"
        }


def integrate_ml_predictions(ticker: str) -> Dict[str, Any]:
    """
    Predictive Analytics: Call ML API for growth rate, cut risk, comprehensive scores.
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        ML predictions dict
    """
    try:
        from app.services.ml_api_client import get_ml_client
        
        ml_client = get_ml_client()
        
        predictions = {}
        
        try:
            growth_response = ml_client.get_yield_forecast([ticker])
            if growth_response.get("success") and growth_response.get("data"):
                growth_data = growth_response["data"][0]
                predictions["growth_rate"] = growth_data.get("predicted_growth_rate")
                predictions["growth_confidence"] = growth_data.get("confidence")
        except Exception as e:
            logger.warning(f"ML growth forecast unavailable for {ticker}: {e}")
            predictions["growth_rate"] = None
        
        try:
            cut_response = ml_client.get_cut_risk([ticker], include_earnings=True)
            if cut_response.get("success") and cut_response.get("data"):
                cut_data = cut_response["data"][0]
                predictions["cut_risk_score"] = cut_data.get("cut_risk_score")
                predictions["risk_level"] = cut_data.get("risk_level")
                predictions["cut_risk_confidence"] = cut_data.get("confidence")
        except Exception as e:
            logger.warning(f"ML cut risk unavailable for {ticker}: {e}")
            predictions["cut_risk_score"] = None
        
        try:
            score_response = ml_client.get_comprehensive_score([ticker])
            if score_response.get("success") and score_response.get("data"):
                score_data = score_response["data"][0]
                predictions["overall_score"] = score_data.get("overall_score")
                predictions["recommendation"] = score_data.get("recommendation")
        except Exception as e:
            logger.warning(f"ML comprehensive score unavailable for {ticker}: {e}")
            predictions["overall_score"] = None
        
        return {
            "ticker": ticker,
            "has_ml_data": any(v is not None for v in predictions.values()),
            "predictions": predictions,
            "source": "HeyDividend Internal ML API"
        }
    
    except Exception as e:
        logger.error(f"Error integrating ML predictions for {ticker}: {e}")
        return {
            "ticker": ticker,
            "has_ml_data": False,
            "predictions": {},
            "source": "ML API unavailable"
        }


def forecast_yield_trajectory(ticker: str, current_yield: float, growth_rate: Optional[float] = None, months_ahead: int = 12) -> Dict[str, Any]:
    """
    Predictive Analytics: Project yield trajectory.
    
    Args:
        ticker: Ticker symbol
        current_yield: Current yield percentage
        growth_rate: Optional growth rate (if None, uses conservative 3%)
        months_ahead: Projection period in months
        
    Returns:
        Yield trajectory forecast dict
    """
    if growth_rate is None:
        growth_rate = 3.0
    
    try:
        monthly_growth = growth_rate / 12 / 100
        
        trajectory = []
        for month in range(months_ahead + 1):
            projected_yield = current_yield * ((1 + monthly_growth) ** month)
            trajectory.append({
                "month": month,
                "projected_yield": round(projected_yield, 2)
            })
        
        final_yield = trajectory[-1]["projected_yield"]
        total_change = final_yield - current_yield
        
        return {
            "ticker": ticker,
            "current_yield": current_yield,
            "growth_rate_used": growth_rate,
            "months_ahead": months_ahead,
            "projected_final_yield": final_yield,
            "total_yield_change": round(total_change, 2),
            "trajectory": trajectory
        }
    
    except Exception as e:
        logger.error(f"Error forecasting yield trajectory for {ticker}: {e}")
        return {
            "ticker": ticker,
            "current_yield": current_yield,
            "error": "Forecast calculation error"
        }


def recommend_action(ticker: str, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prescriptive Analytics: Buy/Hold/Sell/Trim recommendation.
    
    Args:
        ticker: Ticker symbol
        analytics_data: Combined analytics data (descriptive, diagnostic, predictive)
        
    Returns:
        Action recommendation dict
    """
    try:
        consistency_score = analytics_data.get("consistency_score", 50)
        cut_risk = analytics_data.get("cut_risk_score", 0.5)
        yield_value = analytics_data.get("current_yield", 0)
        growth_rate = analytics_data.get("growth_rate", 0)
        
        score = 50
        
        if consistency_score >= 80:
            score += 15
        elif consistency_score >= 60:
            score += 5
        elif consistency_score < 40:
            score -= 15
        
        if cut_risk < 0.2:
            score += 15
        elif cut_risk < 0.4:
            score += 5
        elif cut_risk > 0.7:
            score -= 20
        
        if yield_value > 8:
            score += 10
        elif yield_value > 5:
            score += 5
        
        if growth_rate and growth_rate > 5:
            score += 10
        elif growth_rate and growth_rate < -5:
            score -= 15
        
        if score >= 75:
            recommendation = "BUY"
            rationale = f"Strong fundamentals with {consistency_score}% consistency, low cut risk ({cut_risk:.0%}), and attractive yield ({yield_value:.1f}%)"
        elif score >= 60:
            recommendation = "HOLD"
            rationale = f"Solid performance with {consistency_score}% consistency. Monitor for dividend sustainability"
        elif score >= 40:
            recommendation = "TRIM"
            rationale = f"Moderate risk with {cut_risk:.0%} cut probability. Consider reducing position size"
        else:
            recommendation = "SELL"
            rationale = f"High risk: {cut_risk:.0%} cut probability with {consistency_score}% consistency. Consider alternatives"
        
        return {
            "ticker": ticker,
            "recommendation": recommendation,
            "confidence_score": score,
            "rationale": rationale,
            "key_factors": {
                "consistency": consistency_score,
                "cut_risk": cut_risk,
                "yield": yield_value,
                "growth_rate": growth_rate
            }
        }
    
    except Exception as e:
        logger.error(f"Error generating recommendation for {ticker}: {e}")
        return {
            "ticker": ticker,
            "recommendation": "HOLD",
            "confidence_score": 50,
            "rationale": "Insufficient data for recommendation",
            "key_factors": {}
        }


def suggest_portfolio_adjustments(holdings: List[Dict]) -> Dict[str, Any]:
    """
    Prescriptive Analytics: Portfolio rebalancing and diversification suggestions.
    
    Args:
        holdings: List of portfolio holdings with ticker, shares, value
        
    Returns:
        Portfolio adjustment suggestions dict
    """
    if not holdings:
        return {
            "needs_rebalancing": False,
            "suggestions": [],
            "summary": "No holdings to analyze"
        }
    
    try:
        total_value = sum(h.get("value", 0) for h in holdings)
        
        if total_value == 0:
            return {
                "needs_rebalancing": False,
                "suggestions": [],
                "summary": "Portfolio value is zero"
            }
        
        suggestions = []
        
        for holding in holdings:
            weight = (holding.get("value", 0) / total_value) * 100
            if weight > 25:
                suggestions.append({
                    "type": "trim",
                    "ticker": holding.get("ticker"),
                    "reason": f"Overweight at {weight:.1f}% (target: <25%)",
                    "action": f"Consider trimming {holding.get('ticker')} to reduce concentration risk"
                })
        
        num_holdings = len(holdings)
        if num_holdings < 5:
            suggestions.append({
                "type": "diversify",
                "reason": f"Only {num_holdings} holdings - low diversification",
                "action": "Consider adding 3-5 more dividend payers across different sectors"
            })
        
        needs_rebalancing = len(suggestions) > 0
        
        summary = f"Portfolio has {num_holdings} holdings worth ${total_value:,.2f}. "
        if needs_rebalancing:
            summary += f"{len(suggestions)} adjustment(s) recommended."
        else:
            summary += "Portfolio is well-balanced."
        
        return {
            "needs_rebalancing": needs_rebalancing,
            "suggestions": suggestions,
            "summary": summary,
            "num_holdings": num_holdings,
            "total_value": total_value
        }
    
    except Exception as e:
        logger.error(f"Error suggesting portfolio adjustments: {e}")
        return {
            "needs_rebalancing": False,
            "suggestions": [],
            "summary": "Analysis error"
        }


def prescribe_tax_strategy(ticker: str, holding_period: int, income_amount: float = 0) -> Dict[str, Any]:
    """
    Prescriptive Analytics: Tax optimization recommendations.
    
    Args:
        ticker: Ticker symbol
        holding_period: Days held
        income_amount: Annual dividend income from this holding
        
    Returns:
        Tax strategy recommendations dict
    """
    try:
        is_qualified = holding_period > 60
        
        strategies = []
        
        if is_qualified:
            tax_treatment = "qualified"
            strategies.append({
                "strategy": "Qualified Dividend Treatment",
                "description": f"Held {holding_period} days - eligible for lower qualified dividend tax rates (0%, 15%, or 20%)",
                "priority": "high"
            })
        else:
            tax_treatment = "ordinary"
            days_until_qualified = 61 - holding_period
            strategies.append({
                "strategy": "Hold for Qualified Status",
                "description": f"Hold {days_until_qualified} more days to qualify for lower tax rates",
                "priority": "high"
            })
        
        if ticker.endswith(('Y', 'LY', 'X')):
            strategies.append({
                "strategy": "Tax-Advantaged Account",
                "description": "Option-income ETFs typically generate ordinary income - consider holding in IRA/401(k) to defer taxes",
                "priority": "medium"
            })
        
        if income_amount > 10000:
            strategies.append({
                "strategy": "Tax-Loss Harvesting",
                "description": "High dividend income - consider harvesting losses elsewhere to offset",
                "priority": "medium"
            })
        
        strategies.append({
            "strategy": "DRIP in Taxable Accounts",
            "description": "Reinvesting dividends is still a taxable event - ensure you have cash for tax bill",
            "priority": "low"
        })
        
        return {
            "ticker": ticker,
            "holding_period_days": holding_period,
            "tax_treatment": tax_treatment,
            "is_qualified": is_qualified,
            "strategies": strategies,
            "summary": f"{ticker} dividends taxed as {tax_treatment} income. {len(strategies)} optimization strategies available."
        }
    
    except Exception as e:
        logger.error(f"Error prescribing tax strategy for {ticker}: {e}")
        return {
            "ticker": ticker,
            "tax_treatment": "unknown",
            "strategies": [],
            "summary": "Tax analysis unavailable"
        }


def recommend_income_optimization(portfolio: List[Dict], target_monthly: float) -> Dict[str, Any]:
    """
    Prescriptive Analytics: Income ladder construction recommendations.
    
    Args:
        portfolio: Portfolio holdings
        target_monthly: Target monthly income
        
    Returns:
        Income optimization recommendations dict
    """
    try:
        current_monthly = sum(h.get("monthly_income", 0) for h in portfolio) if portfolio else 0
        
        gap = target_monthly - current_monthly
        
        recommendations = []
        
        if gap > 0:
            recommendations.append({
                "type": "increase_income",
                "description": f"Add ${gap:,.2f}/month to reach target",
                "action": f"Allocate ${gap * 12 / 0.10:,.0f} to 10% yielders or ${gap * 12 / 0.05:,.0f} to 5% yielders"
            })
            
            recommendations.append({
                "type": "ladder_construction",
                "description": "Build monthly income ladder",
                "action": "Diversify across monthly payers (JEPI, TSLY, YMAX, QQQY, XDTE) for consistent cash flow"
            })
        elif gap < -500:
            recommendations.append({
                "type": "excess_income",
                "description": f"Exceeding target by ${abs(gap):,.2f}/month",
                "action": "Consider reinvesting excess or increasing target"
            })
        
        if not portfolio or len(portfolio) < 3:
            recommendations.append({
                "type": "diversification",
                "description": "Low diversification",
                "action": "Add at least 3-5 different dividend payers across sectors"
            })
        
        summary = f"Current: ${current_monthly:,.2f}/mo. Target: ${target_monthly:,.2f}/mo. "
        if gap > 0:
            summary += f"Shortfall: ${gap:,.2f}/mo."
        else:
            summary += "Target met."
        
        return {
            "current_monthly_income": current_monthly,
            "target_monthly_income": target_monthly,
            "income_gap": gap,
            "recommendations": recommendations,
            "summary": summary
        }
    
    except Exception as e:
        logger.error(f"Error recommending income optimization: {e}")
        return {
            "current_monthly_income": 0,
            "target_monthly_income": target_monthly,
            "recommendations": [],
            "summary": "Analysis error"
        }


def suggest_risk_mitigation(ticker: str, cut_risk_score: float) -> Dict[str, Any]:
    """
    Prescriptive Analytics: Actions to reduce dividend cut exposure.
    
    Args:
        ticker: Ticker symbol
        cut_risk_score: Cut risk score (0-1, higher = more risk)
        
    Returns:
        Risk mitigation suggestions dict
    """
    try:
        risk_level = "low" if cut_risk_score < 0.3 else "medium" if cut_risk_score < 0.6 else "high"
        
        mitigations = []
        
        if cut_risk_score > 0.7:
            mitigations.append({
                "priority": "urgent",
                "action": "Reduce Position",
                "description": f"Very high cut risk ({cut_risk_score:.0%}) - consider reducing position by 50%+ immediately"
            })
            
            mitigations.append({
                "priority": "high",
                "action": "Set Price Alert",
                "description": "Monitor closely - set alerts for price drops >10% as early warning signal"
            })
        
        elif cut_risk_score > 0.4:
            mitigations.append({
                "priority": "medium",
                "action": "Monitor Closely",
                "description": f"Moderate cut risk ({cut_risk_score:.0%}) - set up dividend change alerts"
            })
            
            mitigations.append({
                "priority": "medium",
                "action": "Diversify",
                "description": "Don't over-concentrate in this ticker - limit to <15% of portfolio"
            })
        
        else:
            mitigations.append({
                "priority": "low",
                "action": "Routine Monitoring",
                "description": f"Low cut risk ({cut_risk_score:.0%}) - quarterly review is sufficient"
            })
        
        mitigations.append({
            "priority": "low",
            "action": "Review Fundamentals",
            "description": "Check earnings, cash flow, and payout ratio quarterly"
        })
        
        if ticker.endswith(('Y', 'LY', 'X')):
            mitigations.append({
                "priority": "medium",
                "action": "Volatility Awareness",
                "description": "Option-income strategy - distributions vary with market volatility (expected behavior)"
            })
        
        return {
            "ticker": ticker,
            "cut_risk_score": cut_risk_score,
            "risk_level": risk_level,
            "mitigations": mitigations,
            "summary": f"{ticker} has {risk_level} cut risk ({cut_risk_score:.0%}). {len(mitigations)} mitigation strategies recommended."
        }
    
    except Exception as e:
        logger.error(f"Error suggesting risk mitigation for {ticker}: {e}")
        return {
            "ticker": ticker,
            "cut_risk_score": cut_risk_score,
            "risk_level": "unknown",
            "mitigations": [],
            "summary": "Risk analysis unavailable"
        }


def _detect_frequency(dates: List[dt.date]) -> str:
    """Helper: Detect payment frequency from dates."""
    if len(dates) < 2:
        return "irregular"
    
    sorted_dates = sorted(dates)
    intervals = [(sorted_dates[i+1] - sorted_dates[i]).days for i in range(len(sorted_dates)-1)]
    
    if not intervals:
        return "irregular"
    
    avg_interval = statistics.mean(intervals)
    
    if 25 <= avg_interval <= 35:
        return "monthly"
    elif 85 <= avg_interval <= 95:
        return "quarterly"
    elif 175 <= avg_interval <= 190:
        return "semi-annual"
    elif 350 <= avg_interval <= 380:
        return "annual"
    else:
        return "irregular"
