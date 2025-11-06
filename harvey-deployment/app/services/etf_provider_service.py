"""
ETF Provider Service for Harvey AI

Handles queries about ETF providers and their distributions.
Maps providers to their ETF tickers and fetches comprehensive distribution data.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger("etf_provider_service")


class ETFProviderService:
    """
    Service for handling ETF provider-level queries.
    
    Provides comprehensive distribution data for all ETFs from a given provider.
    """
    
    # Major ETF providers and their ticker mappings
    ETF_PROVIDERS = {
        "yieldmax": {
            "name": "YieldMax",
            "tickers": [
                "TSLY", "NVDY", "AAPY", "MSTY", "CONY", "YMAG", "AMDY", "AMDL", 
                "GOOGL", "MSFL", "NFLY", "OARK", "PYPY", "FBY", "NETY", "DISO",
                "SQY", "MRNY", "APLY", "GOOY", "JPMY", "TSMY", "AMZY", "BABO",
                "CRSH", "FANG", "GDXY", "SNOY", "SPKY", "XOMO", "YBIT", "YMAX"
            ],
            "frequency": "monthly",
            "description": "Synthetic covered call ETFs providing high monthly income"
        },
        "global x": {
            "name": "Global X",
            "tickers": [
                "QYLD", "XYLD", "RYLD", "JEPI", "JEPQ", "DJIA", "PFFD", "SDIV",
                "DIV", "QDIV", "RDIV", "TDIV", "XYLG", "QYLG", "RYLG", "HYLG",
                "FYLG", "TYLG", "OYLG", "DYLG", "SYLG", "CLM", "CRF", "DIVB"
            ],
            "frequency": "monthly",
            "description": "Covered call and high dividend ETFs"
        },
        "jpmorgan": {
            "name": "JPMorgan",
            "tickers": [
                "JEPI", "JEPQ", "JPIE", "JPEM", "JPEF", "JPGL", "JPGB", "JPIB",
                "JPST", "JMST", "JPUS", "JPMB", "JMBS", "JPLD", "JCPB", "JAGG"
            ],
            "frequency": "monthly/quarterly",
            "description": "Equity premium income and fixed income ETFs"
        },
        "invesco": {
            "name": "Invesco",
            "tickers": [
                "PBW", "PKW", "PGX", "PFIG", "PFF", "PHB", "PCY", "PICB", "PSK",
                "PZA", "PGHY", "PHDG", "PVI", "PWZ", "PID", "KBWD", "KBWB", "KBWY"
            ],
            "frequency": "monthly/quarterly",
            "description": "Preferred stock and high yield ETFs"
        },
        "wisdomtree": {
            "name": "WisdomTree",
            "tickers": [
                "DHS", "DTD", "DTN", "DES", "DEW", "DLS", "DON", "DIM", "DOL",
                "DWM", "DEM", "DGS", "DGRW", "DGRS", "DGRE", "DLN", "DXJS", "DXUS"
            ],
            "frequency": "quarterly",
            "description": "Dividend and earnings weighted ETFs"
        },
        "proshares": {
            "name": "ProShares",
            "tickers": [
                "HDGE", "NOBL", "REGL", "SMDV", "EFAD", "EUDV", "EFDL", "IHDG",
                "QAI", "HDG", "TMDV", "UMDV", "XRLV", "XMLV", "XSLV", "TOLZ"
            ],
            "frequency": "quarterly",
            "description": "Dividend aristocrats and low volatility ETFs"
        },
        "vanguard": {
            "name": "Vanguard",
            "tickers": [
                "VYM", "VIG", "VYMI", "VIGI", "VDC", "VPU", "VNQ", "VNQI", "VTEB",
                "VCSH", "VCIT", "VCLT", "VGSH", "VGIT", "VGLT", "VMBS", "BND", "BNDX"
            ],
            "frequency": "quarterly",
            "description": "Dividend appreciation and income ETFs"
        },
        "blackrock": {
            "name": "BlackRock/iShares",
            "tickers": [
                "HDV", "DVY", "DGRO", "IDV", "IHDG", "PFF", "HYG", "EMB", "MUB",
                "TIP", "SHY", "IEF", "TLT", "AGG", "LQD", "MBB", "GOVT", "IGSB"
            ],
            "frequency": "monthly/quarterly",
            "description": "Core dividend and fixed income ETFs"
        },
        "spdr": {
            "name": "SPDR",
            "tickers": [
                "SDY", "DGRW", "SPYD", "SPDW", "EDIV", "WDIV", "DWX", "DES", "DVYE",
                "DTD", "KBWD", "KBWY", "RWR", "RWX", "JNK", "SJNK", "SRLN", "FLRN"
            ],
            "frequency": "monthly/quarterly",
            "description": "Dividend and sector ETFs"
        },
        "schwab": {
            "name": "Charles Schwab",
            "tickers": [
                "SCHD", "SCHV", "SCHB", "SCHM", "SCHA", "SCHG", "SCHX", "SCHE",
                "SCHF", "SCHC", "SCHH", "SCHZ", "SCHR", "SCHI", "SCHO", "SCHP"
            ],
            "frequency": "quarterly",
            "description": "Strategic beta and fundamental index ETFs"
        },
        "first trust": {
            "name": "First Trust",
            "tickers": [
                "FVD", "FDL", "FDN", "FXU", "FXD", "FXG", "FXR", "FXZ", "FXH",
                "FXN", "FXO", "FCF", "FEP", "FNI", "FTHI", "FTLS", "FTSL", "FMB"
            ],
            "frequency": "quarterly",
            "description": "AlphaDEX and sector rotation ETFs"
        },
        "amplify": {
            "name": "Amplify",
            "tickers": [
                "YYY", "DIVO", "IDVO", "IQDV", "QDVO"
            ],
            "frequency": "monthly",
            "description": "High income and covered call ETFs"
        },
        "roundhill": {
            "name": "Roundhill",
            "tickers": [
                "QDTE", "XDTE", "RDTE", "TDTE", "ODTE"
            ],
            "frequency": "daily/weekly",
            "description": "Daily/weekly option income ETFs"
        },
        "defiance": {
            "name": "Defiance",
            "tickers": [
                "JEPY", "QQQY", "SPYT", "IWMY", "DIPS", "PUTS"
            ],
            "frequency": "monthly",
            "description": "Next-gen option income ETFs"
        },
        "rexshares": {
            "name": "REX Shares",
            "tickers": [
                "FEPI", "SVOL"
            ],
            "frequency": "monthly",
            "description": "Income and volatility strategies"
        }
    }
    
    # Common aliases and variations
    PROVIDER_ALIASES = {
        "yieldmax": ["yieldmax", "yield max", "ym"],
        "global x": ["global x", "globalx", "gx"],
        "jpmorgan": ["jpmorgan", "jp morgan", "jpm", "chase"],
        "invesco": ["invesco", "powershares"],
        "wisdomtree": ["wisdomtree", "wisdom tree", "wt"],
        "proshares": ["proshares", "pro shares"],
        "vanguard": ["vanguard", "vg"],
        "blackrock": ["blackrock", "black rock", "ishares", "i shares"],
        "spdr": ["spdr", "spider", "state street"],
        "schwab": ["schwab", "charles schwab", "cs"],
        "first trust": ["first trust", "firsttrust", "ft"],
        "amplify": ["amplify"],
        "roundhill": ["roundhill", "round hill"],
        "defiance": ["defiance"],
        "rexshares": ["rexshares", "rex shares", "rex"]
    }
    
    def __init__(self):
        self._build_ticker_to_provider_map()
    
    def _build_ticker_to_provider_map(self):
        """Build reverse mapping from ticker to provider."""
        self.ticker_to_provider = {}
        for provider_key, provider_info in self.ETF_PROVIDERS.items():
            for ticker in provider_info["tickers"]:
                self.ticker_to_provider[ticker] = provider_key
    
    def identify_provider(self, query: str) -> Optional[str]:
        """
        Identify ETF provider from user query.
        
        Args:
            query: User's query text
            
        Returns:
            Provider key if found, None otherwise
        """
        query_lower = query.lower()
        
        # Check each provider's aliases
        for provider_key, aliases in self.PROVIDER_ALIASES.items():
            for alias in aliases:
                if alias in query_lower:
                    logger.info(f"Identified provider: {provider_key} from query")
                    return provider_key
        
        # Check if query contains a ticker that maps to a provider
        words = query.upper().split()
        for word in words:
            # Clean up word (remove punctuation)
            ticker = ''.join(c for c in word if c.isalnum())
            if ticker in self.ticker_to_provider:
                provider = self.ticker_to_provider[ticker]
                logger.info(f"Identified provider {provider} from ticker {ticker}")
                return provider
        
        return None
    
    def get_provider_etfs(self, provider_key: str) -> Optional[Dict[str, Any]]:
        """
        Get all ETFs for a given provider.
        
        Args:
            provider_key: Provider identifier
            
        Returns:
            Dict with provider info and ticker list, or None if not found
        """
        if provider_key not in self.ETF_PROVIDERS:
            logger.warning(f"Unknown provider: {provider_key}")
            return None
        
        return self.ETF_PROVIDERS[provider_key]
    
    def is_provider_query(self, query: str) -> bool:
        """
        Check if query is asking about multiple ETFs from a provider.
        
        Args:
            query: User's query text
            
        Returns:
            True if query is about multiple ETFs from a provider
        """
        query_lower = query.lower()
        
        # Keywords that indicate multiple ETFs
        plural_indicators = ["etfs", "funds", "all", "distribution amounts", "distributions"]
        
        # Check if query mentions a provider and has plural indicators
        provider = self.identify_provider(query)
        if provider:
            for indicator in plural_indicators:
                if indicator in query_lower:
                    return True
        
        # Check for explicit provider ETF queries
        for provider_name in self.PROVIDER_ALIASES.keys():
            for alias in self.PROVIDER_ALIASES[provider_name]:
                if alias in query_lower and any(ind in query_lower for ind in plural_indicators):
                    return True
        
        return False
    
    def format_provider_response(self, provider_key: str, distributions: List[Dict]) -> str:
        """
        Format distribution data for all ETFs from a provider.
        
        Args:
            provider_key: Provider identifier
            distributions: List of distribution records for provider's ETFs
            
        Returns:
            Formatted response string
        """
        provider_info = self.ETF_PROVIDERS.get(provider_key)
        if not provider_info:
            return "Provider information not available."
        
        # Group distributions by ticker
        ticker_distributions = {}
        for dist in distributions:
            ticker = dist.get("Ticker") or dist.get("ticker")
            if ticker:
                if ticker not in ticker_distributions:
                    ticker_distributions[ticker] = []
                ticker_distributions[ticker].append(dist)
        
        # Build response
        response_parts = []
        response_parts.append(f"## {provider_info['name']} ETF Distributions\n")
        response_parts.append(f"**Provider Description:** {provider_info['description']}\n")
        response_parts.append(f"**Distribution Frequency:** {provider_info['frequency'].title()}\n")
        response_parts.append(f"**Total ETFs Tracked:** {len(provider_info['tickers'])}\n\n")
        
        if ticker_distributions:
            response_parts.append("### Latest Distribution Data\n\n")
            response_parts.append("| Ticker | Distribution Amount | Ex-Dividend Date | Yield | Frequency |\n")
            response_parts.append("|--------|-------------------|------------------|-------|-----------|")
            
            for ticker in sorted(ticker_distributions.keys()):
                latest_dist = ticker_distributions[ticker][0]  # Most recent
                amount = latest_dist.get("Distribution_Amount") or latest_dist.get("Dividend_Amount", "N/A")
                ex_date = latest_dist.get("Ex_Dividend_Date") or latest_dist.get("Ex_Date", "N/A")
                yield_val = latest_dist.get("Yield", "N/A")
                freq = provider_info['frequency']
                
                # Format dates properly
                if ex_date != "N/A" and hasattr(ex_date, 'strftime'):
                    ex_date = ex_date.strftime("%Y-%m-%d")
                elif isinstance(ex_date, str) and "T" in ex_date:
                    ex_date = ex_date.split("T")[0]
                
                response_parts.append(f"\n| {ticker} | ${amount:.4f} | {ex_date} | {yield_val} | {freq} |")
        else:
            response_parts.append("\nNo recent distribution data available for this provider's ETFs.")
        
        # Add summary statistics
        if ticker_distributions:
            response_parts.append(f"\n\n### Summary\n")
            response_parts.append(f"- **ETFs with Recent Distributions:** {len(ticker_distributions)}\n")
            response_parts.append(f"- **Average Distribution:** ${sum(float(d[0].get('Distribution_Amount', 0)) for d in ticker_distributions.values()) / len(ticker_distributions):.4f}\n")
            
            # Note about missing ETFs
            missing_etfs = set(provider_info['tickers']) - set(ticker_distributions.keys())
            if missing_etfs:
                response_parts.append(f"- **ETFs without recent data:** {', '.join(sorted(missing_etfs)[:5])}")
                if len(missing_etfs) > 5:
                    response_parts.append(f" (and {len(missing_etfs) - 5} more)")
                response_parts.append("\n")
        
        response_parts.append(f"\n*Note: {provider_info['name']} ETFs typically distribute {provider_info['frequency']}.*")
        
        return ''.join(response_parts)
    
    def get_all_providers(self) -> List[str]:
        """Get list of all supported ETF providers."""
        return list(self.ETF_PROVIDERS.keys())
    
    def search_ticker_provider(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Find which provider a ticker belongs to.
        
        Args:
            ticker: ETF ticker symbol
            
        Returns:
            Provider info if found
        """
        ticker_upper = ticker.upper()
        provider_key = self.ticker_to_provider.get(ticker_upper)
        
        if provider_key:
            return {
                "provider_key": provider_key,
                "provider_info": self.ETF_PROVIDERS[provider_key],
                "ticker": ticker_upper
            }
        
        return None