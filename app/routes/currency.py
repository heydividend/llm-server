"""
Currency conversion API endpoints for Harvey
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.services.currency_service import get_currency_service, SUPPORTED_CURRENCIES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/currency", tags=["currency"])


class ConversionRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str = "USD"


class DividendConversionRequest(BaseModel):
    dividend_amount: float
    native_currency: str
    target_currency: str = "USD"


class MultiCurrencyAggregationRequest(BaseModel):
    dividends: List[dict]  # List of {"amount": float, "currency": str}
    target_currency: str = "USD"


@router.get("/supported")
async def get_supported_currencies():
    """Get list of supported currencies"""
    return {
        "currencies": SUPPORTED_CURRENCIES,
        "total": len(SUPPORTED_CURRENCIES)
    }


@router.get("/rate/{from_currency}/{to_currency}")
async def get_exchange_rate(from_currency: str, to_currency: str):
    """
    Get current exchange rate between two currencies
    
    Example: GET /v1/currency/rate/GBP/USD
    """
    service = get_currency_service()
    rate = service.get_exchange_rate(from_currency, to_currency)
    
    if rate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exchange rate not available for {from_currency}/{to_currency}"
        )
    
    return {
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "rate": rate,
        "formatted": f"1 {from_currency.upper()} = {rate:.6f} {to_currency.upper()}"
    }


@router.post("/convert")
async def convert_currency(request: ConversionRequest):
    """
    Convert amount from one currency to another
    
    Example: POST /v1/currency/convert
    {
        "amount": 100,
        "from_currency": "GBP",
        "to_currency": "USD"
    }
    """
    service = get_currency_service()
    converted = service.convert(request.amount, request.from_currency, request.to_currency)
    
    if converted is None:
        raise HTTPException(
            status_code=404,
            detail=f"Currency conversion failed for {request.from_currency}/{request.to_currency}"
        )
    
    rate = service.get_exchange_rate(request.from_currency, request.to_currency)
    
    return {
        "original_amount": request.amount,
        "original_currency": request.from_currency.upper(),
        "converted_amount": round(converted, 2),
        "converted_currency": request.to_currency.upper(),
        "exchange_rate": rate,
        "formatted": service.format_amount(converted, request.to_currency)
    }


@router.post("/convert-dividend")
async def convert_dividend(request: DividendConversionRequest):
    """
    Convert dividend amount with detailed metadata
    
    Example: POST /v1/currency/convert-dividend
    {
        "dividend_amount": 0.50,
        "native_currency": "GBP",
        "target_currency": "USD"
    }
    """
    service = get_currency_service()
    result = service.convert_dividend(
        request.dividend_amount,
        request.native_currency,
        request.target_currency
    )
    
    return result


@router.post("/aggregate")
async def aggregate_multi_currency(request: MultiCurrencyAggregationRequest):
    """
    Aggregate dividends from multiple currencies
    
    Example: POST /v1/currency/aggregate
    {
        "dividends": [
            {"amount": 100, "currency": "USD"},
            {"amount": 50, "currency": "GBP"},
            {"amount": 75, "currency": "CAD"}
        ],
        "target_currency": "USD"
    }
    """
    service = get_currency_service()
    result = service.aggregate_multi_currency_dividends(
        request.dividends,
        request.target_currency
    )
    
    return {
        **result,
        "formatted_total": service.format_amount(result["total"], request.target_currency)
    }


@router.post("/clear-cache")
async def clear_exchange_rate_cache():
    """Clear the exchange rate cache (admin function)"""
    service = get_currency_service()
    service.clear_cache()
    
    return {
        "success": True,
        "message": "Exchange rate cache cleared"
    }
