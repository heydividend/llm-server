"""
Tests for ETF Provider Service
"""

import pytest
from datetime import datetime, date
from app.services.etf_provider_service import ETFProviderService


class TestETFProviderService:
    """Test suite for ETF provider service functionality."""
    
    @pytest.fixture
    def provider_service(self):
        """Create ETF provider service instance."""
        return ETFProviderService()
    
    def test_identify_provider_direct_name(self, provider_service):
        """Test identifying provider from direct name mention."""
        assert provider_service.identify_provider("YieldMax ETFs") == "yieldmax"
        assert provider_service.identify_provider("What are Global X distributions?") == "global x"
        assert provider_service.identify_provider("Show me Vanguard funds") == "vanguard"
        assert provider_service.identify_provider("iShares dividend ETFs") == "blackrock"
    
    def test_identify_provider_from_ticker(self, provider_service):
        """Test identifying provider from ticker symbol."""
        assert provider_service.identify_provider("What about TSLY?") == "yieldmax"
        assert provider_service.identify_provider("SCHD distribution") == "schwab"
        assert provider_service.identify_provider("Tell me about JEPI and JEPQ") == "jpmorgan"
        assert provider_service.identify_provider("QYLD details") == "global x"
    
    def test_identify_provider_aliases(self, provider_service):
        """Test provider identification with aliases."""
        assert provider_service.identify_provider("JP Morgan funds") == "jpmorgan"
        assert provider_service.identify_provider("wisdom tree ETFs") == "wisdomtree"
        assert provider_service.identify_provider("Charles Schwab distributions") == "schwab"
        assert provider_service.identify_provider("ProShares dividend funds") == "proshares"
    
    def test_is_provider_query_positive(self, provider_service):
        """Test detecting provider-level queries."""
        assert provider_service.is_provider_query("What are the latest distribution amounts for YieldMax ETFs?")
        assert provider_service.is_provider_query("Show all Global X funds")
        assert provider_service.is_provider_query("List all Vanguard ETFs distributions")
        assert provider_service.is_provider_query("Give me all iShares dividend funds")
    
    def test_is_provider_query_negative(self, provider_service):
        """Test rejecting non-provider queries."""
        assert not provider_service.is_provider_query("What is TSLY distribution?")
        assert not provider_service.is_provider_query("SCHD dividend amount")
        assert not provider_service.is_provider_query("Tell me about JEPI")
        assert not provider_service.is_provider_query("What's the yield?")
    
    def test_get_provider_etfs(self, provider_service):
        """Test retrieving ETF list for providers."""
        # YieldMax
        yieldmax_info = provider_service.get_provider_etfs("yieldmax")
        assert yieldmax_info is not None
        assert yieldmax_info["name"] == "YieldMax"
        assert "TSLY" in yieldmax_info["tickers"]
        assert "NVDY" in yieldmax_info["tickers"]
        assert yieldmax_info["frequency"] == "monthly"
        
        # Schwab
        schwab_info = provider_service.get_provider_etfs("schwab")
        assert schwab_info is not None
        assert "SCHD" in schwab_info["tickers"]
        
        # Invalid provider
        assert provider_service.get_provider_etfs("invalid_provider") is None
    
    def test_search_ticker_provider(self, provider_service):
        """Test finding provider from ticker."""
        # YieldMax ticker
        result = provider_service.search_ticker_provider("TSLY")
        assert result is not None
        assert result["provider_key"] == "yieldmax"
        assert result["ticker"] == "TSLY"
        
        # Schwab ticker
        result = provider_service.search_ticker_provider("schd")  # Test case insensitive
        assert result is not None
        assert result["provider_key"] == "schwab"
        assert result["ticker"] == "SCHD"
        
        # Unknown ticker
        assert provider_service.search_ticker_provider("INVALID") is None
    
    def test_format_provider_response(self, provider_service):
        """Test formatting provider distribution response."""
        # Mock distribution data
        distributions = [
            {
                "Ticker": "TSLY",
                "Distribution_Amount": 0.5432,
                "Ex_Dividend_Date": datetime(2024, 1, 15),
                "Yield": "42.5%"
            },
            {
                "Ticker": "NVDY",
                "Distribution_Amount": 0.3876,
                "Ex_Dividend_Date": datetime(2024, 1, 15),
                "Yield": "38.2%"
            }
        ]
        
        response = provider_service.format_provider_response("yieldmax", distributions)
        
        # Check response contains key elements
        assert "YieldMax ETF Distributions" in response
        assert "TSLY" in response
        assert "NVDY" in response
        assert "$0.5432" in response
        assert "$0.3876" in response
        assert "2024-01-15" in response
        assert "Monthly" in response
        assert "Synthetic covered call ETFs" in response
    
    def test_format_provider_response_empty(self, provider_service):
        """Test formatting response with no distribution data."""
        response = provider_service.format_provider_response("yieldmax", [])
        
        assert "YieldMax ETF Distributions" in response
        assert "No recent distribution data available" in response
    
    def test_get_all_providers(self, provider_service):
        """Test getting list of all supported providers."""
        providers = provider_service.get_all_providers()
        
        # Check major providers are included
        assert "yieldmax" in providers
        assert "vanguard" in providers
        assert "schwab" in providers
        assert "blackrock" in providers
        assert "global x" in providers
        assert "jpmorgan" in providers
        assert len(providers) >= 10  # We have at least 10 providers
    
    def test_ticker_to_provider_mapping(self, provider_service):
        """Test the reverse ticker mapping is built correctly."""
        # Check some key mappings exist
        assert "TSLY" in provider_service.ticker_to_provider
        assert "SCHD" in provider_service.ticker_to_provider
        assert "VYM" in provider_service.ticker_to_provider
        assert "JEPI" in provider_service.ticker_to_provider
        
        # Verify mappings are correct
        assert provider_service.ticker_to_provider["TSLY"] == "yieldmax"
        assert provider_service.ticker_to_provider["SCHD"] == "schwab"
        assert provider_service.ticker_to_provider["VYM"] == "vanguard"
    
    def test_comprehensive_provider_coverage(self, provider_service):
        """Test that we have comprehensive ETF provider coverage."""
        # Test each provider has required fields
        for provider_key in provider_service.ETF_PROVIDERS:
            provider_info = provider_service.ETF_PROVIDERS[provider_key]
            assert "name" in provider_info
            assert "tickers" in provider_info
            assert "frequency" in provider_info
            assert "description" in provider_info
            assert len(provider_info["tickers"]) > 0
            assert provider_info["name"]
            assert provider_info["frequency"]
            assert provider_info["description"]
    
    def test_provider_query_edge_cases(self, provider_service):
        """Test edge cases in provider query detection."""
        # Mixed case
        assert provider_service.is_provider_query("YiElDmAx ETFs distributions")
        
        # With punctuation
        assert provider_service.is_provider_query("YieldMax ETFs: what are the distributions?")
        
        # Multiple providers mentioned
        result = provider_service.identify_provider("Compare YieldMax and Global X")
        assert result in ["yieldmax", "global x"]  # Should identify at least one