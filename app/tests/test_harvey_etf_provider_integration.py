"""
Integration tests for Harvey's ETF Provider handling
"""

import pytest
import asyncio
from datetime import datetime
from app.services.harvey_intelligence import HarveyIntelligence


class TestHarveyETFProviderIntegration:
    """Test suite for Harvey's ETF provider integration."""
    
    @pytest.fixture
    def harvey(self):
        """Create Harvey intelligence instance."""
        return HarveyIntelligence()
    
    @pytest.mark.asyncio
    async def test_yieldmax_provider_query(self, harvey):
        """Test Harvey handles YieldMax ETF provider queries correctly."""
        query = "What are the latest distribution amounts for YieldMax ETFs?"
        
        result = await harvey.analyze_dividend(query)
        
        # Verify the response structure
        assert result is not None
        assert "ai_response" in result
        assert "provider_detected" in result
        assert result["provider_detected"] is True
        assert result.get("provider_key") == "yieldmax"
        assert result.get("provider_name") == "YieldMax"
        
        # Verify the response contains YieldMax information
        response = result["ai_response"]
        assert "YieldMax ETF Distributions" in response
        assert "Synthetic covered call ETFs" in response
        assert "monthly" in response.lower()
        
        # Verify it mentions multiple ETFs, not just one
        assert "TSLY" in response or "Total ETFs Tracked" in response
        assert result.get("etfs_count", 0) > 1
    
    @pytest.mark.asyncio
    async def test_vanguard_provider_query(self, harvey):
        """Test Harvey handles Vanguard ETF provider queries correctly."""
        query = "Show me all Vanguard ETFs distributions"
        
        result = await harvey.analyze_dividend(query)
        
        assert result["provider_detected"] is True
        assert result.get("provider_key") == "vanguard"
        assert result.get("provider_name") == "Vanguard"
        
        # Verify the response contains Vanguard-specific info
        response = result["ai_response"]
        assert "Vanguard ETF Distributions" in response
        assert "quarterly" in response.lower()
    
    @pytest.mark.asyncio
    async def test_global_x_provider_query(self, harvey):
        """Test Harvey handles Global X ETF provider queries correctly."""
        query = "List all Global X funds and their distributions"
        
        result = await harvey.analyze_dividend(query)
        
        assert result["provider_detected"] is True
        assert result.get("provider_key") == "global x"
        assert result.get("provider_name") == "Global X"
        
        # Verify the response structure
        response = result["ai_response"]
        assert "Global X ETF Distributions" in response
    
    @pytest.mark.asyncio
    async def test_single_etf_query_not_provider(self, harvey):
        """Test that single ETF queries don't trigger provider response."""
        query = "What is TSLY distribution?"
        
        result = await harvey.analyze_dividend(query, symbol="TSLY")
        
        # This should NOT be detected as a provider query
        # It should go through normal dividend analysis
        assert "provider_detected" not in result or result.get("provider_detected") is False
        assert "model_used" in result
        assert result["symbol"] == "TSLY"
    
    @pytest.mark.asyncio
    async def test_schwab_provider_by_ticker(self, harvey):
        """Test Harvey identifies provider from ticker mention in plural context."""
        query = "Show all distributions for Schwab ETFs including SCHD"
        
        result = await harvey.analyze_dividend(query)
        
        assert result["provider_detected"] is True
        assert result.get("provider_key") == "schwab"
        assert result.get("provider_name") == "Charles Schwab"
        
        response = result["ai_response"]
        assert "SCHD" in response
    
    @pytest.mark.asyncio
    async def test_unknown_provider_query(self, harvey):
        """Test Harvey handles unknown provider gracefully."""
        query = "What are all the FakeProvider ETFs distributions?"
        
        result = await harvey.analyze_dividend(query)
        
        # Should not detect a valid provider
        if result.get("provider_detected"):
            assert result["provider_detected"] is False
        else:
            # Or it should route to regular analysis
            assert "model_used" in result
    
    @pytest.mark.asyncio
    async def test_provider_response_formatting(self, harvey):
        """Test the formatting of provider responses."""
        query = "What are the latest distribution amounts for YieldMax ETFs?"
        
        result = await harvey.analyze_dividend(query)
        
        response = result["ai_response"]
        
        # Check for key formatting elements
        assert "ETF Distributions" in response
        assert "Provider Description:" in response or "Synthetic" in response
        assert "Distribution Frequency:" in response or "monthly" in response.lower()
        
        # Should have table format or structured data
        assert "|" in response or "Ticker" in response
    
    @pytest.mark.asyncio
    async def test_multiple_provider_mentions(self, harvey):
        """Test handling when multiple providers are mentioned."""
        query = "Compare YieldMax and Global X ETFs distributions"
        
        result = await harvey.analyze_dividend(query)
        
        # Should detect at least one provider
        if result.get("provider_detected"):
            assert result["provider_key"] in ["yieldmax", "global x"]
    
    @pytest.mark.asyncio
    async def test_provider_with_specific_question(self, harvey):
        """Test provider query with specific distribution question."""
        query = "Which YieldMax ETFs have the highest distributions?"
        
        result = await harvey.analyze_dividend(query)
        
        assert result["provider_detected"] is True
        assert result.get("provider_key") == "yieldmax"
        
        # Should provide YieldMax-specific data
        response = result["ai_response"]
        assert "YieldMax" in response
        assert result.get("etfs_count", 0) > 1