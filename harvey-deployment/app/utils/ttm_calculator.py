"""
TTM (Trailing Twelve Months) distribution calculator for dividend income tracking.
"""

import datetime as dt
from typing import Optional, Dict, List, Tuple, Any
from decimal import Decimal
import logging

logger = logging.getLogger("ai_controller")


def calculate_ttm_distributions(
    shares: int, 
    ticker: str, 
    distribution_history: List[Dict],
    reference_date: Optional[dt.date] = None
) -> Dict[str, Any]:
    """
    Calculate TTM (trailing twelve months) distributions for a given holding.
    
    Args:
        shares: Number of shares owned
        ticker: Ticker symbol
        distribution_history: List of distribution records with 'Dividend_Amount' and 'Payment_Date' or 'Ex_Dividend_Date'
        reference_date: Reference date for TTM calculation (defaults to today)
    
    Returns:
        Dictionary with:
            - ttm_total: Total distributions in last 12 months
            - monthly_avg: Average monthly distribution
            - num_payments: Number of payments in TTM period
            - annual_income: Total annual income (shares * ttm_total)
            - monthly_income: Average monthly income (annual_income / 12)
            - payments: List of individual payments in TTM period
    
    Example:
        >>> history = [
        ...     {'Dividend_Amount': 0.25, 'Payment_Date': dt.date(2024, 11, 15)},
        ...     {'Dividend_Amount': 0.25, 'Payment_Date': dt.date(2024, 10, 15)},
        ... ]
        >>> result = calculate_ttm_distributions(200, 'YMAX', history)
        >>> print(f"Annual income: ${result['annual_income']:.2f}")
    """
    if reference_date is None:
        reference_date = dt.date.today()
    
    ttm_start = reference_date - dt.timedelta(days=365)
    
    ttm_payments = []
    ttm_total = Decimal('0.00')
    
    for record in distribution_history:
        try:
            dividend_amount = record.get('Dividend_Amount') or record.get('AdjDividend_Amount') or record.get('Distribution_Amount')
            
            if dividend_amount is None:
                continue
            
            dividend_amount = Decimal(str(dividend_amount))
            
            payment_date = record.get('Payment_Date') or record.get('Ex_Dividend_Date') or record.get('Ex_Date')
            
            if payment_date is None:
                continue
            
            if isinstance(payment_date, str):
                payment_date = dt.datetime.fromisoformat(payment_date.replace('Z', '+00:00')).date()
            elif isinstance(payment_date, dt.datetime):
                payment_date = payment_date.date()
            
            if ttm_start <= payment_date <= reference_date:
                ttm_total += dividend_amount
                ttm_payments.append({
                    'date': payment_date,
                    'amount': float(dividend_amount)
                })
        
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Error processing distribution record for {ticker}: {e}")
            continue
    
    num_payments = len(ttm_payments)
    monthly_avg = float(ttm_total) / 12 if ttm_total > 0 else 0.0
    
    annual_income = shares * float(ttm_total)
    monthly_income = annual_income / 12
    
    return {
        'ticker': ticker,
        'shares': shares,
        'ttm_total': float(ttm_total),
        'monthly_avg': monthly_avg,
        'num_payments': num_payments,
        'annual_income': annual_income,
        'monthly_income': monthly_income,
        'payments': sorted(ttm_payments, key=lambda x: x['date'], reverse=True),
        'period_start': ttm_start,
        'period_end': reference_date
    }


def format_ttm_result(ttm_data: Dict) -> str:
    """
    Format TTM calculation result as a readable message.
    
    Args:
        ttm_data: Dictionary returned by calculate_ttm_distributions
    
    Returns:
        Formatted string with TTM income details
    """
    ticker = ttm_data['ticker']
    shares = ttm_data['shares']
    annual_income = ttm_data['annual_income']
    monthly_income = ttm_data['monthly_income']
    num_payments = ttm_data['num_payments']
    
    message = (
        f"💰 **With {shares:,} shares of {ticker}, you received ${annual_income:,.2f} "
        f"in the last 12 months (${monthly_income:,.2f} per month on average)**\n\n"
    )
    
    if num_payments > 0:
        message += f"This is based on {num_payments} dividend payment(s) in the TTM period."
    else:
        message += "⚠️ No dividend payments found in the last 12 months."
    
    return message


def format_ttm_summary(ttm_data: Dict, include_details: bool = False) -> str:
    """
    Format a concise TTM summary.
    
    Args:
        ttm_data: Dictionary returned by calculate_ttm_distributions
        include_details: Whether to include payment details
    
    Returns:
        Formatted summary string
    """
    ticker = ttm_data['ticker']
    shares = ttm_data['shares']
    annual_income = ttm_data['annual_income']
    monthly_income = ttm_data['monthly_income']
    num_payments = ttm_data['num_payments']
    
    summary = f"**{ticker}**: {shares:,} shares → ${annual_income:,.2f}/year (${monthly_income:,.2f}/month)"
    
    if include_details and num_payments > 0:
        summary += f"\n- {num_payments} payments in last 12 months"
        if ttm_data.get('payments'):
            summary += "\n- Recent payments:"
            for payment in ttm_data['payments'][:3]:
                summary += f"\n  - {payment['date']}: ${payment['amount']:.2f}"
    
    return summary


def calculate_portfolio_ttm(holdings: List[Dict], distribution_data: Dict[str, List[Dict]]) -> Dict:
    """
    Calculate TTM for an entire portfolio.
    
    Args:
        holdings: List of holdings with 'ticker' and 'shares' keys
        distribution_data: Dictionary mapping ticker -> list of distribution records
    
    Returns:
        Dictionary with portfolio-level TTM data
    """
    portfolio_results = []
    total_annual_income = 0.0
    total_monthly_income = 0.0
    
    for holding in holdings:
        ticker = holding['ticker'].upper()
        shares = holding['shares']
        
        history = distribution_data.get(ticker, [])
        
        ttm_data = calculate_ttm_distributions(shares, ticker, history)
        portfolio_results.append(ttm_data)
        
        total_annual_income += ttm_data['annual_income']
        total_monthly_income += ttm_data['monthly_income']
    
    return {
        'holdings': portfolio_results,
        'total_annual_income': total_annual_income,
        'total_monthly_income': total_monthly_income,
        'num_holdings': len(holdings)
    }


def format_portfolio_ttm_summary(portfolio_data: Dict) -> str:
    """
    Format portfolio TTM summary.
    
    Args:
        portfolio_data: Dictionary returned by calculate_portfolio_ttm
    
    Returns:
        Formatted portfolio summary string
    """
    total_annual = portfolio_data['total_annual_income']
    total_monthly = portfolio_data['total_monthly_income']
    num_holdings = portfolio_data['num_holdings']
    
    summary = f"## 💼 Portfolio TTM Income Summary\n\n"
    summary += f"**Total Annual Income**: ${total_annual:,.2f}\n"
    summary += f"**Average Monthly Income**: ${total_monthly:,.2f}\n"
    summary += f"**Number of Holdings**: {num_holdings}\n\n"
    
    summary += "### Individual Holdings:\n\n"
    for holding_data in portfolio_data['holdings']:
        summary += f"- {format_ttm_summary(holding_data)}\n"
    
    return summary
