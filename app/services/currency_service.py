"""
Currency Conversion Service for Harvey AI
Provides real-time forex rates and multi-currency support

Features:
- Real-time exchange rates from multiple sources
- Intelligent caching (4-hour TTL for forex rates)
- Automatic fallback across multiple forex APIs
- Support for 7+ major currencies (USD, GBP, CAD, AUD, EUR, JPY, HKD)
- Currency-adjusted dividend calculations
- Multi-currency portfolio aggregation
"""

import os
import time
import logging
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Supported currencies for Harvey
SUPPORTED_CURRENCIES = {
    "USD": {"name": "US Dollar", "symbol": "$", "default": True},
    "GBP": {"name": "British Pound", "symbol": "£", "country": "United Kingdom"},
    "CAD": {"name": "Canadian Dollar", "symbol": "C$", "country": "Canada"},
    "AUD": {"name": "Australian Dollar", "symbol": "A$", "country": "Australia"},
    "EUR": {"name": "Euro", "symbol": "€", "country": "European Union"},
    "JPY": {"name": "Japanese Yen", "symbol": "¥", "country": "Japan"},
    "HKD": {"name": "Hong Kong Dollar", "symbol": "HK$", "country": "Hong Kong"}
}

# Forex API endpoints (multiple sources for reliability)
FOREX_APIS = [
    {
        "name": "Frankfurter",
        "url": "https://api.frankfurter.app/latest",
        "free": True,
        "rate_limit": None,
        "parse": lambda data, from_cur, to_cur: data.get("rates", {}).get(to_cur)
    },
    {
        "name": "ExchangeRate-API",
        "url": "https://api.exchangerate-api.com/v4/latest/{currency}",
        "free": True,
        "rate_limit": None,
        "parse": lambda data, from_cur, to_cur: data.get("rates", {}).get(to_cur)
    }
]


class CurrencyService:
    """
    Currency conversion service with intelligent caching and fallback
    """
    
    def __init__(self, cache_ttl_seconds: int = 14400):  # 4 hours default
        """
        Initialize currency service
        
        Args:
            cache_ttl_seconds: Cache time-to-live in seconds (default 4 hours)
        """
        self.cache_ttl = cache_ttl_seconds
        self._rate_cache: Dict[str, Tuple[float, datetime]] = {}
        self._last_update: Optional[datetime] = None
        logger.info(f"CurrencyService initialized (cache_ttl={cache_ttl_seconds}s)")
    
    def get_exchange_rate(
        self, 
        from_currency: str, 
        to_currency: str,
        use_cache: bool = True
    ) -> Optional[float]:
        """
        Get exchange rate between two currencies
        
        Args:
            from_currency: Source currency code (e.g., 'GBP')
            to_currency: Target currency code (e.g., 'USD')
            use_cache: Whether to use cached rates (default True)
            
        Returns:
            Exchange rate or None if unavailable
        """
        # Normalize currency codes
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Same currency = 1.0
        if from_currency == to_currency:
            return 1.0
        
        # Validate currencies
        if from_currency not in SUPPORTED_CURRENCIES or to_currency not in SUPPORTED_CURRENCIES:
            logger.warning(f"Unsupported currency pair: {from_currency}/{to_currency}")
            return None
        
        # Check cache
        cache_key = f"{from_currency}_{to_currency}"
        if use_cache and cache_key in self._rate_cache:
            rate, timestamp = self._rate_cache[cache_key]
            age = (datetime.now() - timestamp).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Cache hit: {cache_key} = {rate} (age={age:.0f}s)")
                return rate
        
        # Fetch from API with fallback
        rate = self._fetch_rate_with_fallback(from_currency, to_currency)
        
        # Cache the result
        if rate is not None:
            self._rate_cache[cache_key] = (rate, datetime.now())
            self._last_update = datetime.now()
            logger.info(f"Fetched rate: {from_currency}/{to_currency} = {rate:.6f}")
        
        return rate
    
    def _fetch_rate_with_fallback(
        self, 
        from_currency: str, 
        to_currency: str
    ) -> Optional[float]:
        """
        Fetch exchange rate with automatic fallback across multiple APIs
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate or None if all APIs fail
        """
        for api in FOREX_APIS:
            try:
                rate = self._fetch_from_api(api, from_currency, to_currency)
                if rate is not None:
                    logger.info(f"Got rate from {api['name']}: {from_currency}/{to_currency} = {rate:.6f}")
                    return rate
            except Exception as e:
                logger.warning(f"{api['name']} failed: {e}")
                continue
        
        logger.error(f"All forex APIs failed for {from_currency}/{to_currency}")
        return None
    
    def _fetch_from_api(
        self, 
        api: Dict, 
        from_currency: str, 
        to_currency: str
    ) -> Optional[float]:
        """
        Fetch rate from a specific API
        
        Args:
            api: API configuration dict
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate or None if fetch fails
        """
        url = api["url"].format(currency=from_currency)
        
        # Add base currency parameter for Frankfurter
        if "frankfurter" in url:
            url = f"{url}?from={from_currency}&to={to_currency}"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        rate = api["parse"](data, from_currency, to_currency)
        
        return float(rate) if rate else None
    
    def convert(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str
    ) -> Optional[float]:
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount or None if rate unavailable
        """
        rate = self.get_exchange_rate(from_currency, to_currency)
        if rate is None:
            return None
        
        return amount * rate
    
    def convert_dividend(
        self,
        dividend_amount: float,
        native_currency: str,
        target_currency: str = "USD"
    ) -> Dict:
        """
        Convert dividend amount with detailed metadata
        
        Args:
            dividend_amount: Dividend amount in native currency
            native_currency: Original currency code
            target_currency: Target currency for conversion (default USD)
            
        Returns:
            Dict with converted amount, rate, and metadata
        """
        rate = self.get_exchange_rate(native_currency, target_currency)
        
        if rate is None:
            return {
                "amount": dividend_amount,
                "currency": native_currency,
                "converted_amount": None,
                "converted_currency": target_currency,
                "exchange_rate": None,
                "error": "Exchange rate unavailable"
            }
        
        converted = dividend_amount * rate
        
        return {
            "amount": dividend_amount,
            "currency": native_currency,
            "converted_amount": round(converted, 2),
            "converted_currency": target_currency,
            "exchange_rate": round(rate, 6),
            "conversion_date": self._last_update.isoformat() if self._last_update else None
        }
    
    def get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol (e.g., '$' for USD, '£' for GBP)"""
        return SUPPORTED_CURRENCIES.get(currency_code.upper(), {}).get("symbol", currency_code)
    
    def get_currency_name(self, currency_code: str) -> str:
        """Get currency full name (e.g., 'US Dollar' for USD)"""
        return SUPPORTED_CURRENCIES.get(currency_code.upper(), {}).get("name", currency_code)
    
    def format_amount(
        self, 
        amount: float, 
        currency: str, 
        show_symbol: bool = True
    ) -> str:
        """
        Format currency amount with proper symbol and formatting
        
        Args:
            amount: Monetary amount
            currency: Currency code
            show_symbol: Whether to include currency symbol
            
        Returns:
            Formatted string (e.g., '$123.45' or '123.45 USD')
        """
        if show_symbol:
            symbol = self.get_currency_symbol(currency)
            return f"{symbol}{amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency.upper()}"
    
    def aggregate_multi_currency_dividends(
        self,
        dividends: list,
        target_currency: str = "USD"
    ) -> Dict:
        """
        Aggregate dividends from multiple currencies into single currency
        
        Args:
            dividends: List of dicts with 'amount' and 'currency' keys
            target_currency: Target currency for aggregation (default USD)
            
        Returns:
            Dict with total, breakdown by currency, and conversion details
        """
        total = 0.0
        breakdown = {}
        conversions = []
        
        for div in dividends:
            amount = div.get("amount", 0)
            currency = div.get("currency", "USD")
            
            converted = self.convert(amount, currency, target_currency)
            
            if converted is not None:
                total += converted
                breakdown[currency] = breakdown.get(currency, 0) + amount
                
                if currency != target_currency:
                    conversions.append({
                        "from_amount": amount,
                        "from_currency": currency,
                        "to_amount": round(converted, 2),
                        "to_currency": target_currency,
                        "rate": self.get_exchange_rate(currency, target_currency)
                    })
        
        return {
            "total": round(total, 2),
            "currency": target_currency,
            "breakdown": breakdown,
            "conversions": conversions,
            "currencies_count": len(breakdown)
        }
    
    def clear_cache(self):
        """Clear the exchange rate cache"""
        self._rate_cache.clear()
        self._last_update = None
        logger.info("Exchange rate cache cleared")


# Global currency service instance
_currency_service: Optional[CurrencyService] = None

def get_currency_service() -> CurrencyService:
    """Get or create global currency service instance"""
    global _currency_service
    if _currency_service is None:
        _currency_service = CurrencyService()
    return _currency_service
