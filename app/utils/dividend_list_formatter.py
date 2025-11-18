"""
Dividend List Table Formatter - Formats dividend lists as markdown tables
Automatically formats dividend stock data into professional tables for Harvey's chat responses
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DividendListFormatter:
    """
    Utility to format dividend lists as markdown tables
    """
    
    @staticmethod
    def format_list_as_table(
        stocks: List[Dict[str, Any]], 
        category_name: str = "Dividend Stocks",
        include_metrics: bool = True
    ) -> str:
        """
        Format dividend list stocks as a professional markdown table
        
        Args:
            stocks: List of stock dictionaries from dividend_list_service
            category_name: Name of the category/list
            include_metrics: Whether to include yield, payout ratio, etc.
            
        Returns:
            Formatted markdown table string
        """
        if not stocks:
            return f"\n**{category_name}**: No stocks found.\n"
        
        # Build table header
        response = f"\n### 📊 {category_name} ({len(stocks)} stocks)\n\n"
        
        # Determine columns based on available data
        has_yield = any(s.get("dividend_yield") for s in stocks)
        has_payout = any(s.get("payout_ratio") for s in stocks)
        has_years = any(s.get("consecutive_years") for s in stocks)
        has_frequency = any(s.get("payment_frequency") for s in stocks)
        
        # Build table header
        if include_metrics:
            header = "| Ticker | Company | Price | Yield"
            separator = "|--------|---------|-------|------"
            
            if has_payout:
                header += " | Payout Ratio"
                separator += "|-------------"
            
            if has_years:
                header += " | Years"
                separator += "|------"
            
            if has_frequency:
                header += " | Frequency"
                separator += "|----------"
            
            header += " |\n"
            separator += "|\n"
        else:
            header = "| Ticker | Company | Price | Yield |\n"
            separator = "|--------|---------|-------|-------|\n"
        
        response += header + separator
        
        # Add rows
        for stock in stocks:
            ticker = stock.get("ticker", "N/A")
            company = stock.get("company_name", ticker)[:30]  # Truncate long names
            price = stock.get("current_price", 0)
            yield_val = stock.get("dividend_yield", 0)
            payout = stock.get("payout_ratio")
            years = stock.get("consecutive_years", 0)
            frequency = stock.get("payment_frequency", "N/A")
            
            # Format row
            row = f"| {ticker} | {company} | ${price:.2f} | {yield_val:.2f}%"
            
            if include_metrics:
                if has_payout:
                    payout_str = f"{payout:.1f}%" if payout is not None else "N/A"
                    row += f" | {payout_str}"
                
                if has_years:
                    row += f" | {years}"
                
                if has_frequency:
                    row += f" | {frequency}"
            
            row += " |\n"
            response += row
        
        # Add summary
        if len(stocks) > 0:
            avg_yield = sum(s.get("dividend_yield", 0) for s in stocks) / len(stocks)
            response += f"\n**Average Yield**: {avg_yield:.2f}%\n"
        
        return response
    
    @staticmethod
    def format_category_summary(category: Dict[str, Any]) -> str:
        """
        Format a category summary with description and criteria
        
        Args:
            category: Category dictionary from dividend_list_service
            
        Returns:
            Formatted category summary
        """
        name = category.get("name", "Category")
        description = category.get("description", "")
        criteria = category.get("criteria", "")
        
        response = f"\n### {name}\n\n"
        
        if description:
            response += f"{description}\n\n"
        
        if criteria:
            response += f"**Selection Criteria**: {criteria}\n\n"
        
        return response
    
    @staticmethod
    def format_all_categories(categories: List[Dict[str, Any]]) -> str:
        """
        Format all available dividend categories as a list
        
        Args:
            categories: List of all category dictionaries
            
        Returns:
            Formatted category list
        """
        if not categories:
            return "\nNo dividend categories available.\n"
        
        response = "\n### 📋 Available Dividend Lists\n\n"
        
        # Group categories by type
        premium_lists = []
        yield_focused = []
        frequency_based = []
        sector_based = []
        other_lists = []
        
        for cat in categories:
            cat_id = cat.get("category_id", "")
            name = cat.get("name", "Unknown")
            description = cat.get("description", "")
            
            if "king" in cat_id.lower() or "aristocrat" in cat_id.lower() or "champion" in cat_id.lower():
                premium_lists.append(cat)
            elif "yield" in cat_id.lower():
                yield_focused.append(cat)
            elif "monthly" in cat_id.lower() or "quarterly" in cat_id.lower():
                frequency_based.append(cat)
            elif "reit" in cat_id.lower() or "utilit" in cat_id.lower():
                sector_based.append(cat)
            else:
                other_lists.append(cat)
        
        # Format each group
        if premium_lists:
            response += "**🏆 Premium Dividend Lists**\n"
            for cat in premium_lists:
                response += f"- **{cat.get('name')}**: {cat.get('description')}\n"
            response += "\n"
        
        if yield_focused:
            response += "**💰 Yield-Focused Lists**\n"
            for cat in yield_focused:
                response += f"- **{cat.get('name')}**: {cat.get('description')}\n"
            response += "\n"
        
        if frequency_based:
            response += "**📅 Payment Frequency Lists**\n"
            for cat in frequency_based:
                response += f"- **{cat.get('name')}**: {cat.get('description')}\n"
            response += "\n"
        
        if sector_based:
            response += "**🏢 Sector-Specific Lists**\n"
            for cat in sector_based:
                response += f"- **{cat.get('name')}**: {cat.get('description')}\n"
            response += "\n"
        
        if other_lists:
            response += "**📊 Other Lists**\n"
            for cat in other_lists:
                response += f"- **{cat.get('name')}**: {cat.get('description')}\n"
            response += "\n"
        
        response += f"\n*Total: {len(categories)} dividend lists available*\n"
        
        return response
    
    @staticmethod
    def detect_list_query(user_query: str) -> Optional[str]:
        """
        Detect if user is asking about a specific dividend list
        
        Args:
            user_query: User's question
            
        Returns:
            Category ID if detected, None otherwise
        """
        query_lower = user_query.lower()
        
        # Mapping of keywords to category IDs
        category_keywords = {
            "dividend_aristocrats": ["aristocrat", "aristocrats", "dividend aristocrat"],
            "dividend_kings": ["dividend king", "kings"],
            "dividend_champions": ["champion", "champions", "dividend champion"],
            "high_yield": ["high yield", "high-yield", "highest yield", "best yield"],
            "monthly_payers": ["monthly dividend", "monthly payer", "pay monthly", "monthly income"],
            "quarterly_growth": ["quarterly growth", "quarterly dividend growth"],
            "reits": ["reit", "real estate", "real estate investment trust"],
            "utilities": ["utilit", "utility stock", "utility dividend"],
            "dividend_etfs": ["dividend etf", "etf"],
            "low_payout_ratio": ["low payout", "conservative payout", "safe payout", "sustainable payout"]
        }
        
        # Check for matches
        for category_id, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return category_id
        
        # Check for generic list queries
        if any(word in query_lower for word in ["show me", "list", "what are", "tell me about"]):
            if "dividend" in query_lower:
                # Generic dividend list query - return None to show all categories
                return "all_categories"
        
        return None
