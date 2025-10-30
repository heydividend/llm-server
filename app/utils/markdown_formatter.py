"""
Professional Markdown Formatter for Harvey
Provides clean, business-grade markdown formatting without emojis or icons.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from py_markdown_table.markdown_table import markdown_table
import mdformat


class ProfessionalMarkdownFormatter:
    """Formats financial data into clean, professional markdown tables."""
    
    @staticmethod
    def format_dividend_table(data: List[Dict[str, Any]]) -> str:
        """
        Format dividend data into a professional table with standardized columns.
        
        Required columns (in order):
        1. Ticker
        2. Price
        3. Distribution Amount
        4. Yield
        5. Payout Ratio
        6. Declaration Date
        7. Ex-Date
        8. Pay Date
        
        Args:
            data: List of dividend data dictionaries
            
        Returns:
            Formatted markdown table string
        """
        if not data:
            return "No dividend data available."
        
        formatted_data = []
        for item in data:
            formatted_row = {
                "Ticker": item.get("ticker", item.get("Ticker", "N/A")),
                "Price": ProfessionalMarkdownFormatter._format_price(item.get("price", item.get("Price"))),
                "Distribution Amount": ProfessionalMarkdownFormatter._format_currency(
                    item.get("distribution_amount", item.get("Distribution Amount", item.get("dividend_amount")))
                ),
                "Yield": ProfessionalMarkdownFormatter._format_percentage(
                    item.get("yield", item.get("Yield", item.get("dividend_yield")))
                ),
                "Payout Ratio": ProfessionalMarkdownFormatter._format_percentage(
                    item.get("payout_ratio", item.get("Payout Ratio"))
                ),
                "Declaration Date": ProfessionalMarkdownFormatter._format_date(
                    item.get("declaration_date", item.get("Declaration Date", item.get("declarationDate")))
                ),
                "Ex-Date": ProfessionalMarkdownFormatter._format_date(
                    item.get("ex_date", item.get("Ex-Date", item.get("exDate", item.get("ex_dividend_date")))
                ),
                "Pay Date": ProfessionalMarkdownFormatter._format_date(
                    item.get("pay_date", item.get("Pay Date", item.get("payDate", item.get("payment_date")))
                )
            }
            formatted_data.append(formatted_row)
        
        table = markdown_table(formatted_data).get_markdown()
        
        return ProfessionalMarkdownFormatter.clean_markdown(table)
    
    @staticmethod
    def format_stock_table(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
        """
        Format stock data into a professional table.
        
        Args:
            data: List of stock data dictionaries
            columns: Optional list of column names to include (in order)
            
        Returns:
            Formatted markdown table string
        """
        if not data:
            return "No data available."
        
        if columns:
            formatted_data = []
            for item in data:
                formatted_row = {}
                for col in columns:
                    col_lower = col.lower().replace(" ", "_")
                    value = item.get(col_lower, item.get(col, "N/A"))
                    
                    if "price" in col.lower() or "value" in col.lower():
                        formatted_row[col] = ProfessionalMarkdownFormatter._format_price(value)
                    elif "yield" in col.lower() or "ratio" in col.lower() or "%" in col.lower():
                        formatted_row[col] = ProfessionalMarkdownFormatter._format_percentage(value)
                    elif "date" in col.lower():
                        formatted_row[col] = ProfessionalMarkdownFormatter._format_date(value)
                    elif "amount" in col.lower():
                        formatted_row[col] = ProfessionalMarkdownFormatter._format_currency(value)
                    else:
                        formatted_row[col] = str(value) if value is not None else "N/A"
                formatted_data.append(formatted_row)
            
            table = markdown_table(formatted_data).get_markdown()
        else:
            table = markdown_table(data).get_markdown()
        
        return ProfessionalMarkdownFormatter.clean_markdown(table)
    
    @staticmethod
    def add_action_prompt(content: str, ticker_list: Optional[List[str]] = None) -> str:
        """
        Add watchlist/portfolio action prompt to response.
        
        Args:
            content: The main response content
            ticker_list: Optional list of tickers mentioned in the response
            
        Returns:
            Content with action prompt appended
        """
        action_section = "\n\n---\n\n**Next Steps:**\n\n"
        
        if ticker_list and len(ticker_list) > 0:
            tickers_str = ", ".join(ticker_list)
            action_section += f"- Add {tickers_str} to your watchlist to monitor price changes and dividend announcements\n"
            action_section += f"- Add {tickers_str} to your portfolio to track performance and income\n"
        else:
            action_section += "- Add stocks to your watchlist to monitor price changes and dividend announcements\n"
            action_section += "- Add stocks to your portfolio to track performance and income\n"
        
        action_section += "- Set up alerts for dividend cuts, yield changes, or price targets\n"
        action_section += "- Build an income ladder for monthly cash flow from quarterly dividend payers\n"
        
        return content + action_section
    
    @staticmethod
    def clean_markdown(text: str) -> str:
        """
        Clean markdown text using mdformat for professional consistency.
        Removes emojis and ensures consistent formatting.
        
        Args:
            text: Raw markdown text
            
        Returns:
            Cleaned, professionally formatted markdown
        """
        if not text:
            return ""
        
        cleaned = ProfessionalMarkdownFormatter._remove_emojis(text)
        
        try:
            cleaned = mdformat.text(cleaned)
        except Exception:
            pass
        
        return cleaned
    
    @staticmethod
    def _remove_emojis(text: str) -> str:
        """Remove emoji characters from text."""
        import re
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U00002600-\U000026FF"  # misc symbols
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)
    
    @staticmethod
    def _format_price(value: Any) -> str:
        """Format price value as currency."""
        if value is None or value == "N/A":
            return "N/A"
        try:
            price = float(value)
            return f"${price:.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _format_currency(value: Any) -> str:
        """Format currency value."""
        if value is None or value == "N/A":
            return "N/A"
        try:
            amount = float(value)
            return f"${amount:.4f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _format_percentage(value: Any) -> str:
        """Format percentage value."""
        if value is None or value == "N/A":
            return "N/A"
        try:
            if isinstance(value, str) and '%' in value:
                return value
            
            pct = float(value)
            if pct > 1:
                return f"{pct:.2f}%"
            else:
                return f"{pct * 100:.2f}%"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _format_date(value: Any) -> str:
        """Format date value."""
        if value is None or value == "N/A":
            return "N/A"
        
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                return value
        
        return str(value)


formatter = ProfessionalMarkdownFormatter()
