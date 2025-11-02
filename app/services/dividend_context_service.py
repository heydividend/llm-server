"""
Dividend Context Service for Harvey AI

Intelligently classifies dividend records and provides context-aware date display logic.
Determines which dates to show based on the dividend's state (declared today, standard, upcoming announcement).
"""

import datetime as dt
import logging
from typing import List, Dict, Optional, Any
from app.utils.dividend_analytics import calculate_next_declaration_date, _detect_frequency
import statistics

logger = logging.getLogger("dividend_context_service")


class DividendContextService:
    """
    Service for enriching dividend data with contextual metadata.
    
    Classifies dividends into states and provides intelligent date display hints.
    """
    
    def __init__(self):
        self._prediction_cache: Dict[str, Dict[str, Any]] = {}
    
    def enrich_dividend_data(
        self, 
        dividends: List[Dict[str, Any]], 
        ticker: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Enrich dividend records with context metadata.
        
        Args:
            dividends: List of dividend records with Declaration_Date, Ex_Dividend_Date, Payment_Date
            ticker: Optional ticker symbol for better logging and caching
            use_cache: Whether to use cached predictions (default: True)
        
        Returns:
            List of enriched dividend records with added 'context' key containing:
                - state: "declared_today", "upcoming_ex_date", "upcoming_payment", "upcoming_announcement", or "standard"
                - declared_today: bool
                - next_decl_date: Optional[date]
                - days_until_ex_date: Optional[int] (when state is "upcoming_ex_date")
                - days_until_payment: Optional[int] (when state is "upcoming_payment")
                - primary_dates: list of date keys to emphasize
                - secondary_dates: list of optional date keys
                - display_hints: dict with rendering suggestions
        """
        if not dividends:
            return []
        
        today = dt.datetime.utcnow().date()
        enriched_dividends = []
        
        ticker_key = ticker or "unknown"
        
        next_decl_prediction = None
        if ticker_key in self._prediction_cache and use_cache:
            next_decl_prediction = self._prediction_cache[ticker_key]
            logger.debug(f"Using cached prediction for {ticker_key}")
        else:
            next_decl_prediction = calculate_next_declaration_date(dividends, ticker_key)
            if next_decl_prediction:
                self._prediction_cache[ticker_key] = next_decl_prediction
                logger.debug(f"Cached new prediction for {ticker_key}")
        
        for dividend in dividends:
            context = self._classify_dividend(dividend, today, next_decl_prediction)
            enriched_dividend = dividend.copy()
            enriched_dividend['context'] = context
            enriched_dividends.append(enriched_dividend)
        
        return enriched_dividends
    
    def _classify_dividend(
        self, 
        dividend: Dict[str, Any], 
        today: dt.date,
        next_decl_prediction: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classify a single dividend record and generate context metadata.
        
        Args:
            dividend: Single dividend record
            today: Today's date for comparison
            next_decl_prediction: Prediction data from calculate_next_declaration_date
        
        Returns:
            Context metadata dict
        """
        declaration_date = self._parse_date(
            dividend.get('Declaration_Date') or dividend.get('declaration_date')
        )
        ex_date = self._parse_date(
            dividend.get('Ex_Dividend_Date') or dividend.get('ex_dividend_date') or dividend.get('Ex_Date')
        )
        pay_date = self._parse_date(
            dividend.get('Payment_Date') or dividend.get('payment_date') or dividend.get('Pay_Date')
        )
        
        declared_today = declaration_date == today if declaration_date else False
        
        # Initialize optional metadata
        days_until_ex_date = None
        days_until_payment = None
        
        if declared_today:
            state = "declared_today"
            primary_dates = ['Declaration_Date', 'Ex_Dividend_Date', 'Payment_Date']
            secondary_dates = []
            display_hints = {
                'show_badge': True,
                'badge_text': '✓ Declared Today',
                'badge_column': 'Declaration_Date',
                'highlight': True
            }
        elif ex_date and ex_date > today and (ex_date - today).days <= 7:
            state = "upcoming_ex_date"
            days_until_ex_date = (ex_date - today).days
            primary_dates = ['Ex_Dividend_Date', 'Payment_Date']
            secondary_dates = ['Declaration_Date']
            display_hints = {
                'show_badge': True,
                'badge_text': f'Ex-Date in {days_until_ex_date} day{"s" if days_until_ex_date != 1 else ""}',
                'badge_column': 'Ex_Dividend_Date',
                'highlight': True,
                'emphasize_ex_date': True
            }
        elif pay_date and pay_date > today and (pay_date - today).days <= 7:
            state = "upcoming_payment"
            days_until_payment = (pay_date - today).days
            primary_dates = ['Payment_Date']
            secondary_dates = ['Ex_Dividend_Date', 'Declaration_Date']
            display_hints = {
                'show_badge': True,
                'badge_text': f'Payment in {days_until_payment} day{"s" if days_until_payment != 1 else ""}',
                'badge_column': 'Payment_Date',
                'highlight': True,
                'emphasize_pay_date': True
            }
        elif ex_date and ex_date > today:
            state = "standard"
            primary_dates = ['Ex_Dividend_Date', 'Payment_Date']
            secondary_dates = ['Declaration_Date']
            display_hints = {
                'show_badge': False,
                'emphasize_ex_date': True,
                'hide_declaration': False
            }
        elif pay_date and pay_date > today:
            state = "standard"
            primary_dates = ['Payment_Date']
            secondary_dates = ['Ex_Dividend_Date', 'Declaration_Date']
            display_hints = {
                'show_badge': False,
                'emphasize_pay_date': True
            }
        else:
            state = "standard"
            primary_dates = ['Ex_Dividend_Date', 'Payment_Date']
            secondary_dates = ['Declaration_Date']
            display_hints = {
                'show_badge': False
            }
        
        next_decl_date = None
        next_decl_date_str = None
        confidence = None
        
        if next_decl_prediction and next_decl_prediction.get('has_prediction'):
            next_decl_date = next_decl_prediction.get('next_ex_date')
            next_decl_date_str = next_decl_prediction.get('next_ex_date_str')
            confidence = next_decl_prediction.get('confidence')
            
            if state == "standard" and not declared_today:
                state = "upcoming_announcement"
                display_hints['show_next_prediction'] = True
                if confidence:
                    display_hints['prediction_confidence'] = confidence
        
        context = {
            'state': state,
            'declared_today': declared_today,
            'next_decl_date': next_decl_date,
            'next_decl_date_str': next_decl_date_str,
            'prediction_confidence': confidence,
            'primary_dates': primary_dates,
            'secondary_dates': secondary_dates,
            'display_hints': display_hints,
            'declaration_date': declaration_date,
            'ex_date': ex_date,
            'pay_date': pay_date
        }
        
        # Add optional days_until metadata when applicable
        if days_until_ex_date is not None:
            context['days_until_ex_date'] = days_until_ex_date
        if days_until_payment is not None:
            context['days_until_payment'] = days_until_payment
        
        return context
    
    def get_declaration_pattern_summary(
        self, 
        dividends: List[Dict[str, Any]], 
        ticker: str
    ) -> Dict[str, Any]:
        """
        Analyze declaration date patterns for a ticker.
        
        Args:
            dividends: List of dividend records
            ticker: Ticker symbol
        
        Returns:
            Dict containing:
                - frequency: detected frequency (monthly, quarterly, etc.)
                - avg_days_between: average days between declarations
                - consistency_score: 0-100 score
                - next_expected_date: predicted next declaration date
                - confidence: prediction confidence level
        """
        if not dividends or len(dividends) < 3:
            return {
                'frequency': 'unknown',
                'avg_days_between': None,
                'consistency_score': 0,
                'next_expected_date': None,
                'confidence': 'low'
            }
        
        try:
            declaration_dates = []
            for div in dividends:
                decl_date = self._parse_date(
                    div.get('Declaration_Date') or div.get('declaration_date')
                )
                if decl_date:
                    declaration_dates.append(decl_date)
            
            if len(declaration_dates) < 3:
                return {
                    'frequency': 'unknown',
                    'avg_days_between': None,
                    'consistency_score': 0,
                    'next_expected_date': None,
                    'confidence': 'low'
                }
            
            frequency = _detect_frequency(declaration_dates)
            
            sorted_dates = sorted(declaration_dates, reverse=True)
            intervals = [(sorted_dates[i] - sorted_dates[i+1]).days for i in range(len(sorted_dates)-1)]
            avg_days = statistics.mean(intervals) if intervals else None
            std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0
            
            cv = (std_dev / avg_days) if avg_days and avg_days > 0 else 1.0
            consistency_score = max(0, min(100, int((1 - min(cv, 1.0)) * 100)))
            
            confidence = "high" if std_dev < 7 else "medium" if std_dev < 14 else "low"
            
            next_expected_date = None
            if avg_days and confidence in ["high", "medium"]:
                latest_date = sorted_dates[0]
                next_expected_date = latest_date + dt.timedelta(days=int(avg_days))
                
                today = dt.datetime.utcnow().date()
                while next_expected_date <= today:
                    next_expected_date = next_expected_date + dt.timedelta(days=int(avg_days))
            
            return {
                'frequency': frequency,
                'avg_days_between': round(avg_days, 1) if avg_days else None,
                'consistency_score': consistency_score,
                'next_expected_date': next_expected_date,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error analyzing declaration pattern for {ticker}: {e}")
            return {
                'frequency': 'error',
                'avg_days_between': None,
                'consistency_score': 0,
                'next_expected_date': None,
                'confidence': 'low'
            }
    
    def clear_cache(self, ticker: Optional[str] = None):
        """
        Clear prediction cache for a specific ticker or all tickers.
        
        Args:
            ticker: Optional ticker to clear. If None, clears entire cache.
        """
        if ticker:
            self._prediction_cache.pop(ticker, None)
            logger.info(f"Cleared cache for {ticker}")
        else:
            self._prediction_cache.clear()
            logger.info("Cleared entire prediction cache")
    
    @staticmethod
    def _parse_date(date_value: Any) -> Optional[dt.date]:
        """
        Parse a date value into a datetime.date object.
        
        Args:
            date_value: Date as string, datetime, or date object
        
        Returns:
            datetime.date object or None
        """
        if date_value is None:
            return None
        
        if isinstance(date_value, dt.date):
            return date_value
        
        if isinstance(date_value, dt.datetime):
            return date_value.date()
        
        if isinstance(date_value, str):
            try:
                parsed = dt.datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return parsed.date()
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse date string: {date_value}")
                return None
        
        return None


_service_instance = None

def get_dividend_context_service() -> DividendContextService:
    """
    Get singleton instance of DividendContextService.
    
    Returns:
        DividendContextService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = DividendContextService()
    return _service_instance
