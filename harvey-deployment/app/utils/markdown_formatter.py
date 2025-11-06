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
    def format_dividend_table(data: List[Dict[str, Any]], use_context: bool = False) -> str:
        """
        Format dividend data into a professional table with standardized columns.
        
        Required columns (in order):
        1. Ticker
        2. Price
        3. Distribution
        4. Yield
        5. Payout Ratio
        6. Declaration
        7. Ex-Date
        8. Pay Date
        
        Args:
            data: List of dividend data dictionaries
            use_context: If True and data contains 'context' metadata, use context-aware rendering
            
        Returns:
            Formatted markdown table string with proper header separators
        """
        if not data:
            return "No dividend data available."
        
        has_context = use_context and any(item.get('context') for item in data)
        
        show_declaration = True
        show_ex_date = True
        show_pay_date = True
        
        if has_context:
            has_declared_today = any(
                item.get('context', {}).get('declared_today', False) 
                for item in data
            )
            
            if not has_declared_today:
                all_standard = all(
                    item.get('context', {}).get('state') == 'standard' 
                    for item in data if item.get('context')
                )
                if all_standard:
                    show_declaration = False
        
        formatted_data = []
        next_prediction_info = None
        
        for item in data:
            # Handle various column name variations (case-insensitive matching)
            item_lower = {k.lower(): v for k, v in item.items()}
            
            # Ticker
            ticker = (item.get("ticker") or item.get("Ticker") or 
                     item.get("symbol") or item.get("Symbol") or
                     item_lower.get("ticker") or item_lower.get("symbol") or "N/A")
            
            # Price
            price = (item.get("price") or item.get("Price") or 
                    item.get("current_price") or item.get("Current Price") or
                    item_lower.get("price") or item_lower.get("current_price"))
            
            # Distribution Amount
            distribution = (item.get("Dividend_Amount") or  # Match exact SQL column name
                          item.get("distribution_amount") or 
                          item.get("Distribution Amount") or 
                          item.get("dividend_amount") or 
                          item.get("Dividend Amount") or
                          item.get("amount") or item.get("Amount") or
                          item_lower.get("distribution_amount") or
                          item_lower.get("dividend_amount") or
                          item_lower.get("amount"))
            
            # Yield
            yield_val = (item.get("yield") or item.get("Yield") or 
                        item.get("dividend_yield") or item.get("Dividend Yield") or
                        item.get("current_yield") or item.get("Current Yield") or
                        item_lower.get("yield") or item_lower.get("dividend_yield") or
                        item_lower.get("current_yield"))
            
            # Payout Ratio
            payout = (item.get("payout_ratio") or item.get("Payout Ratio") or
                     item.get("payoutratio") or item.get("PayoutRatio") or
                     item_lower.get("payout_ratio") or item_lower.get("payoutratio"))
            
            # Declaration Date
            decl_date = (item.get("Declaration_Date") or  # Match exact SQL column name
                        item.get("declaration_date") or 
                        item.get("Declaration Date") or 
                        item.get("declarationDate") or
                        item.get("declarationdate") or
                        item.get("DeclarationDate") or
                        item_lower.get("declaration_date") or
                        item_lower.get("declarationdate"))
            
            # Ex-Date
            ex_date = (item.get("Ex_Dividend_Date") or  # Match exact SQL column name
                      item.get("ex_date") or item.get("Ex-Date") or 
                      item.get("exDate") or item.get("exdate") or
                      item.get("ex_dividend_date") or 
                      item.get("Ex Dividend Date") or
                      item.get("ExDate") or
                      item_lower.get("ex_date") or item_lower.get("exdate") or
                      item_lower.get("ex_dividend_date"))
            
            # Pay Date
            pay_date = (item.get("Payment_Date") or  # Match exact SQL column name
                       item.get("pay_date") or item.get("Pay Date") or 
                       item.get("payDate") or item.get("paydate") or
                       item.get("payment_date") or 
                       item.get("Payment Date") or
                       item.get("PayDate") or
                       item_lower.get("pay_date") or item_lower.get("paydate") or
                       item_lower.get("payment_date"))
            
            context = item.get('context', {}) if has_context else {}
            declared_today = context.get('declared_today', False)
            
            formatted_decl_date = ProfessionalMarkdownFormatter._format_date(decl_date)
            if declared_today and formatted_decl_date != "N/A":
                formatted_decl_date = f"{formatted_decl_date} ✓"
            
            if context.get('next_decl_date_str') and not next_prediction_info:
                next_prediction_info = {
                    'ticker': ticker,
                    'next_date': context.get('next_decl_date_str'),
                    'confidence': context.get('prediction_confidence', 'medium')
                }
            
            formatted_row = {
                "Ticker": str(ticker) if ticker and ticker != "N/A" else "N/A",
                "Price": ProfessionalMarkdownFormatter._format_price(price),
                "Distribution": ProfessionalMarkdownFormatter._format_currency(distribution),
                "Yield": ProfessionalMarkdownFormatter._format_percentage(yield_val),
                "Payout Ratio": ProfessionalMarkdownFormatter._format_percentage(payout),
            }
            
            if show_declaration:
                formatted_row["Declaration"] = formatted_decl_date
            
            if show_ex_date:
                formatted_row["Ex-Date"] = ProfessionalMarkdownFormatter._format_date(ex_date)
            
            if show_pay_date:
                formatted_row["Pay Date"] = ProfessionalMarkdownFormatter._format_date(pay_date)
            
            formatted_data.append(formatted_row)
        
        # Generate markdown table (py-markdown-table automatically adds header separators)
        table = markdown_table(formatted_data).set_params(
            row_sep='markdown',
            quote=False
        ).get_markdown()
        
        # Don't use clean_markdown here as mdformat can sometimes break table formatting
        # Remove emojis only if not using context (to preserve checkmarks and other intentional symbols)
        if not has_context:
            table = ProfessionalMarkdownFormatter._remove_emojis(table)
        
        if next_prediction_info:
            confidence_label = {
                'high': 'High confidence',
                'medium': 'Medium confidence',
                'low': 'Low confidence'
            }.get(next_prediction_info['confidence'], 'Medium confidence')
            
            table += f"\n\n**Next Expected Declaration:** {next_prediction_info['next_date']} ({confidence_label})"
        
        return table
    
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
