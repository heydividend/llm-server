#!/usr/bin/env python
"""
Test ML Schedulers Integration

Tests the newly integrated ML scheduler functionality
"""

import asyncio
import logging
from datetime import datetime
from app.services.ml_schedulers_service import MLSchedulersService
from app.services.ml_integration import get_ml_integration

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_schedulers_service():
    """Test ML schedulers service directly"""
    logger.info("=" * 60)
    logger.info("Testing ML Schedulers Service")
    logger.info("=" * 60)
    
    service = MLSchedulersService()
    
    # Test symbols
    test_symbols = ["MSFT", "AAPL", "JNJ", "O", "SCHD"]
    
    # 1. Test health status
    logger.info("\n1. Testing health status...")
    health = await service.get_health_status()
    logger.info(f"Health Status: {health}")
    
    # 2. Test payout ratings
    logger.info("\n2. Testing payout ratings...")
    payout_ratings = await service.get_payout_ratings(test_symbols)
    logger.info(f"Payout Ratings Success: {payout_ratings.get('success', False)}")
    if payout_ratings.get("success"):
        for symbol, rating in payout_ratings.get("ratings", {}).items():
            logger.info(f"  {symbol}: {rating.get('grade', 'N/A')} "
                       f"(Score: {rating.get('score', 0):.2f})")
    
    # 3. Test dividend calendar
    logger.info("\n3. Testing dividend calendar predictions...")
    calendar = await service.get_dividend_calendar(test_symbols, months_ahead=3)
    logger.info(f"Calendar Predictions Success: {calendar.get('success', False)}")
    if calendar.get("success"):
        for symbol, pred in calendar.get("predictions", {}).items():
            logger.info(f"  {symbol}: Next ex-date: {pred.get('next_ex_date', 'N/A')}")
    
    # 4. Test training status
    logger.info("\n4. Testing training status...")
    training = await service.get_training_status()
    logger.info(f"Training Status: {training.get('status', 'unknown')}")
    logger.info(f"  Next training: {training.get('next_training', 'N/A')}")
    logger.info(f"  Models trained: {training.get('models_trained', [])}")


async def test_ml_integration():
    """Test ML integration with scheduler methods"""
    logger.info("=" * 60)
    logger.info("Testing ML Integration with Schedulers")
    logger.info("=" * 60)
    
    ml_integration = get_ml_integration()
    
    # Test symbols
    test_symbols = ["MSFT", "AAPL", "JNJ", "O", "SCHD"]
    
    # 1. Test scheduled payout ratings
    logger.info("\n1. Testing scheduled payout ratings...")
    payout_ratings = await ml_integration.get_scheduled_payout_ratings(test_symbols)
    logger.info(f"Payout Ratings Success: {payout_ratings.get('success', False)}")
    
    # 2. Test dividend calendar predictions
    logger.info("\n2. Testing dividend calendar predictions...")
    calendar = await ml_integration.get_dividend_calendar_predictions(test_symbols, months_ahead=6)
    logger.info(f"Calendar Success: {calendar.get('success', False)}")
    
    # 3. Test ML training status
    logger.info("\n3. Testing ML training status...")
    training_status = await ml_integration.get_ml_training_status()
    logger.info(f"Training Status: {training_status.get('status', 'unknown')}")
    
    # 4. Test scheduler health
    logger.info("\n4. Testing scheduler health...")
    health = await ml_integration.get_scheduler_health()
    logger.info(f"Scheduler Health: {health}")


async def test_fastapi_endpoints():
    """Test FastAPI endpoints for ML schedulers"""
    logger.info("=" * 60)
    logger.info("Testing FastAPI Endpoints")
    logger.info("=" * 60)
    
    import httpx
    
    # Base URL for local testing
    base_url = "http://localhost:8001/v1/ml-schedulers"
    
    async with httpx.AsyncClient() as client:
        # 1. Test health endpoint
        logger.info("\n1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            logger.info(f"Health Response: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"  Data: {response.json()}")
        except Exception as e:
            logger.error(f"Health endpoint error: {e}")
        
        # 2. Test payout ratings endpoint
        logger.info("\n2. Testing payout ratings endpoint...")
        try:
            response = await client.post(
                f"{base_url}/payout-ratings",
                json={"symbols": ["MSFT", "AAPL", "JNJ"]}
            )
            logger.info(f"Payout Ratings Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  Success: {data.get('success', False)}")
        except Exception as e:
            logger.error(f"Payout ratings endpoint error: {e}")
        
        # 3. Test dividend calendar endpoint
        logger.info("\n3. Testing dividend calendar endpoint...")
        try:
            response = await client.post(
                f"{base_url}/dividend-calendar",
                json={"symbols": ["O", "SCHD"], "months_ahead": 3}
            )
            logger.info(f"Calendar Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  Success: {data.get('success', False)}")
        except Exception as e:
            logger.error(f"Calendar endpoint error: {e}")
        
        # 4. Test training status endpoint
        logger.info("\n4. Testing training status endpoint...")
        try:
            response = await client.get(f"{base_url}/training-status")
            logger.info(f"Training Status Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  Status: {data.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"Training status endpoint error: {e}")


async def main():
    """Run all tests"""
    logger.info("Starting ML Scheduler Integration Tests")
    logger.info(f"Time: {datetime.utcnow().isoformat()}")
    
    # Test the service layer
    await test_schedulers_service()
    
    # Test the ML integration layer
    await test_ml_integration()
    
    # Test the FastAPI endpoints (requires server running)
    logger.info("\n" + "=" * 60)
    logger.info("Note: FastAPI endpoint tests require server running on port 8001")
    logger.info("=" * 60)
    # Uncomment to test endpoints:
    # await test_fastapi_endpoints()
    
    logger.info("\n" + "=" * 60)
    logger.info("ML Scheduler Integration Tests Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())