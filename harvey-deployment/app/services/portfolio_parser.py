"""
Portfolio & Watchlist Parser Service

Handles parsing portfolio data from various formats:
- CSV files (with different column configurations)
- Excel spreadsheets
- PDF brokerage statements
- Images/screenshots of portfolio pages
- Text extracts from any source

Normalizes data into a standard format for Harvey to analyze.
"""

import re
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple
from io import StringIO
from dataclasses import dataclass

logger = logging.getLogger("portfolio_parser")


@dataclass
class PortfolioHolding:
    """Standardized portfolio holding"""
    ticker: str
    shares: Optional[float] = None
    average_cost: Optional[float] = None
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    last_dividend: Optional[float] = None
    description: Optional[str] = None
    exchange: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "shares": self.shares,
            "average_cost": self.average_cost,
            "current_price": self.current_price,
            "current_value": self.current_value,
            "last_dividend": self.last_dividend,
            "description": self.description,
            "exchange": self.exchange
        }


class PortfolioParser:
    """
    Multi-format portfolio data parser.
    
    Handles:
    - CSV files with various column names
    - Extracted text from PDFs/images
    - Tables from OCR results
    - Various ticker formats
    """
    
    # Column name mappings (case-insensitive)
    TICKER_COLUMNS = ["symbol", "ticker", "stock", "security"]
    SHARES_COLUMNS = ["shares", "quantity", "qty", "current shares", "position"]
    PRICE_COLUMNS = ["price", "current price", "last price", "market price"]
    COST_COLUMNS = ["cost", "average cost", "avg cost", "cost basis", "purchase price"]
    VALUE_COLUMNS = ["value", "current value", "market value", "total value"]
    DIVIDEND_COLUMNS = ["dividend", "last div", "last dividend", "distribution"]
    NAME_COLUMNS = ["name", "description", "company", "security name"]
    
    def __init__(self):
        self.ticker_pattern = re.compile(r'\b([A-Z]{1,5})\b')
        self.ticker_with_exchange = re.compile(r'\(([A-Z]+):([A-Z]+)\)')
    
    def extract_ticker_from_text(self, text: str) -> Optional[str]:
        """
        Extract ticker from various formats:
        - Simple: AAPL
        - With exchange: (ARCX:NVDY)
        - Full name: "YieldMax NVDA Opt In Str (ARCX:NVDY)"
        """
        text = text.strip()
        
        # Check for exchange format first: (ARCX:NVDY)
        exchange_match = self.ticker_with_exchange.search(text)
        if exchange_match:
            return exchange_match.group(2)  # Return ticker part
        
        # Check for simple ticker format (1-5 uppercase letters)
        words = text.split()
        for word in words:
            word_clean = word.strip('(),.:;')
            if self.ticker_pattern.fullmatch(word_clean):
                # Filter out common non-ticker words
                if word_clean not in ['INC', 'CORP', 'CO', 'THE', 'ETF', 'FUND', 'LP', 'LLC']:
                    return word_clean
        
        return None
    
    def parse_csv_text(self, csv_text: str, rid: Optional[str] = None) -> List[PortfolioHolding]:
        """
        Parse CSV text into portfolio holdings.
        Handles various column name formats.
        """
        tag = f"[{rid}]" if rid else "[portfolio_parser]"
        holdings = []
        
        try:
            # Try different delimiters
            delimiter = ','
            if '\t' in csv_text:
                delimiter = '\t'
            
            csv_reader = csv.DictReader(StringIO(csv_text), delimiter=delimiter)
            
            # Normalize column names (lowercase, strip whitespace)
            rows = []
            for row in csv_reader:
                normalized_row = {k.lower().strip(): v.strip() for k, v in row.items() if k}
                rows.append(normalized_row)
            
            if not rows:
                logger.warning(f"{tag} No rows found in CSV")
                return holdings
            
            # Identify column mappings
            first_row = rows[0]
            column_map = self._identify_columns(first_row)
            
            logger.info(f"{tag} CSV column mapping: {column_map}")
            
            # Parse each row
            for i, row in enumerate(rows, 1):
                try:
                    holding = self._parse_row(row, column_map, tag)
                    if holding:
                        holdings.append(holding)
                except Exception as e:
                    logger.warning(f"{tag} Failed to parse row {i}: {e}")
                    continue
            
            logger.info(f"{tag} Parsed {len(holdings)} holdings from CSV")
            
        except Exception as e:
            logger.error(f"{tag} CSV parsing failed: {e}")
        
        return holdings
    
    def _identify_columns(self, sample_row: Dict[str, str]) -> Dict[str, str]:
        """Identify which columns contain which data types"""
        column_map = {}
        
        for col_name, value in sample_row.items():
            col_lower = col_name.lower()
            
            # Check ticker columns
            if any(name in col_lower for name in self.TICKER_COLUMNS):
                column_map['ticker'] = col_name
            
            # Check shares columns
            elif any(name in col_lower for name in self.SHARES_COLUMNS):
                column_map['shares'] = col_name
            
            # Check price columns
            elif any(name in col_lower for name in self.PRICE_COLUMNS):
                column_map['price'] = col_name
            
            # Check cost columns
            elif any(name in col_lower for name in self.COST_COLUMNS):
                column_map['cost'] = col_name
            
            # Check value columns
            elif any(name in col_lower for name in self.VALUE_COLUMNS):
                column_map['value'] = col_name
            
            # Check dividend columns
            elif any(name in col_lower for name in self.DIVIDEND_COLUMNS):
                column_map['dividend'] = col_name
            
            # Check name/description columns
            elif any(name in col_lower for name in self.NAME_COLUMNS):
                column_map['name'] = col_name
        
        return column_map
    
    def _parse_row(self, row: Dict[str, str], column_map: Dict[str, str], tag: str) -> Optional[PortfolioHolding]:
        """Parse a single CSV row into a PortfolioHolding"""
        
        # Extract ticker
        ticker = None
        if 'ticker' in column_map:
            ticker_text = row.get(column_map['ticker'], '')
            ticker = self.extract_ticker_from_text(ticker_text)
        
        # Fallback: try to find ticker in any column
        if not ticker:
            for col_name, value in row.items():
                if value:
                    ticker = self.extract_ticker_from_text(value)
                    if ticker:
                        break
        
        if not ticker:
            logger.warning(f"{tag} No ticker found in row: {row}")
            return None
        
        # Extract numeric values
        shares = self._parse_number(row.get(column_map.get('shares', ''), ''))
        price = self._parse_number(row.get(column_map.get('price', ''), ''))
        cost = self._parse_number(row.get(column_map.get('cost', ''), ''))
        value = self._parse_number(row.get(column_map.get('value', ''), ''))
        dividend = self._parse_number(row.get(column_map.get('dividend', ''), ''))
        
        # Extract description
        description = row.get(column_map.get('name', ''), '') or None
        
        # Extract exchange if present in ticker text
        exchange = None
        if 'ticker' in column_map:
            ticker_text = row.get(column_map['ticker'], '')
            exchange_match = self.ticker_with_exchange.search(ticker_text)
            if exchange_match:
                exchange = exchange_match.group(1)
        
        return PortfolioHolding(
            ticker=ticker,
            shares=shares,
            current_price=price,
            average_cost=cost,
            current_value=value,
            last_dividend=dividend,
            description=description,
            exchange=exchange
        )
    
    def _parse_number(self, value: str) -> Optional[float]:
        """Parse a number from various formats"""
        if not value:
            return None
        
        try:
            # Remove common formatting
            cleaned = value.strip().replace('$', '').replace(',', '').replace('%', '')
            
            # Handle negative numbers in parentheses
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def parse_extracted_text(self, text: str, rid: Optional[str] = None) -> List[PortfolioHolding]:
        """
        Parse portfolio data from extracted text (OCR, PDF, etc.).
        Attempts multiple parsing strategies.
        """
        tag = f"[{rid}]" if rid else "[portfolio_parser]"
        
        # Strategy 1: Check if it's CSV-like text
        if ',' in text or '\t' in text:
            holdings = self.parse_csv_text(text, rid)
            if holdings:
                logger.info(f"{tag} Successfully parsed as CSV-like text")
                return holdings
        
        # Strategy 2: Extract tickers and numbers from freeform text
        holdings = self._parse_freeform_text(text, tag)
        
        return holdings
    
    def _parse_freeform_text(self, text: str, tag: str) -> List[PortfolioHolding]:
        """
        Parse portfolio data from freeform text using pattern matching.
        Looks for patterns like: TICKER 100 $50.00
        """
        holdings = []
        lines = text.split('\n')
        
        # Pattern: Ticker followed by numbers
        # Example: AAPL 100 150.25
        # Example: MSFT    50    $280.75
        pattern = re.compile(r'\b([A-Z]{1,5})\b\s+(\d+(?:\.\d+)?)\s+\$?(\d+(?:\.\d+)?)')
        
        for line in lines:
            matches = pattern.findall(line)
            for ticker, shares, price in matches:
                # Filter out non-ticker words
                if ticker in ['INC', 'CORP', 'CO', 'THE', 'ETF', 'FUND', 'LP', 'LLC', 'TOTAL']:
                    continue
                
                holding = PortfolioHolding(
                    ticker=ticker,
                    shares=float(shares),
                    current_price=float(price)
                )
                holdings.append(holding)
        
        if holdings:
            logger.info(f"{tag} Extracted {len(holdings)} holdings from freeform text")
        
        return holdings
    
    def format_holdings_summary(self, holdings: List[PortfolioHolding]) -> str:
        """
        Format holdings into a readable summary for Harvey to analyze.
        """
        if not holdings:
            return "No portfolio holdings detected."
        
        summary = f"**PORTFOLIO ANALYSIS ({len(holdings)} holdings detected)**\n\n"
        
        # Group by whether we have full data or partial
        full_data = [h for h in holdings if h.shares and (h.current_price or h.current_value)]
        partial_data = [h for h in holdings if h not in full_data]
        
        if full_data:
            summary += "**Complete Holdings:**\n\n"
            summary += "| Ticker | Shares | Price | Value | Avg Cost | Last Div |\n"
            summary += "|--------|--------|-------|-------|----------|----------|\n"
            
            for h in full_data:
                value = h.current_value or (h.shares * h.current_price if h.current_price else None)
                summary += f"| {h.ticker} | {h.shares or '-'} | "
                summary += f"${h.current_price:.2f} | " if h.current_price else "- | "
                summary += f"${value:.2f} | " if value else "- | "
                summary += f"${h.average_cost:.2f} | " if h.average_cost else "- | "
                summary += f"${h.last_dividend:.4f} |\n" if h.last_dividend else "- |\n"
        
        if partial_data:
            summary += "\n**Additional Tickers (partial data):**\n"
            for h in partial_data:
                summary += f"- {h.ticker}"
                if h.shares:
                    summary += f" ({h.shares} shares)"
                if h.description:
                    summary += f" - {h.description}"
                summary += "\n"
        
        # Calculate totals if possible
        total_value = sum(h.current_value or (h.shares * h.current_price if h.shares and h.current_price else 0) 
                         for h in full_data)
        
        if total_value > 0:
            summary += f"\n**Total Portfolio Value: ${total_value:,.2f}**\n"
        
        return summary
    
    def extract_tickers_list(self, holdings: List[PortfolioHolding]) -> List[str]:
        """Extract just the ticker symbols as a list"""
        return [h.ticker for h in holdings if h.ticker]


# Global instance
portfolio_parser = PortfolioParser()
