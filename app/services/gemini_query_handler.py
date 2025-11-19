"""
Gemini Query Handler for Harvey AI
Specialized handling for Gemini-routed query types with custom prompts and processing.

Handles:
- Dividend Sustainability Analysis
- Risk Assessment
- Portfolio Optimization
- Tax Strategy
- Global Dividend Markets
- Multimodal Document Analysis
"""

import logging
import base64
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from app.services.gemini_client import get_gemini_client
from app.core.model_router import QueryType

logger = logging.getLogger("gemini_query_handler")


class GeminiQueryHandler:
    """
    Handles Gemini-specific query processing with specialized prompts and formatting.
    """
    
    def __init__(self):
        """Initialize Gemini query handler."""
        self.client = get_gemini_client()
        self.prompts = self._init_specialized_prompts()
        logger.info("GeminiQueryHandler initialized")
    
    def _init_specialized_prompts(self) -> Dict[QueryType, str]:
        """
        Initialize specialized system prompts for each query type.
        
        Returns:
            Dict mapping QueryType to specialized system prompts
        """
        return {
            QueryType.DIVIDEND_SUSTAINABILITY: """You are Harvey, an expert dividend sustainability analyst.

Your role is to provide **deep, comprehensive analysis** of dividend sustainability using fundamental analysis.

When analyzing dividend sustainability, focus on:

1. **Payout Ratio Analysis**
   - Current payout ratio vs. industry average
   - Historical payout ratio trends (5+ years)
   - Free cash flow payout ratio (most reliable metric)
   
2. **Earnings Coverage**
   - Dividend coverage by earnings (earnings per share / dividend per share)
   - Consistency of earnings growth
   - Earnings stability during downturns
   
3. **Cash Flow Analysis**
   - Free cash flow generation
   - Operating cash flow trends
   - Capital expenditure requirements
   
4. **Balance Sheet Health**
   - Debt levels (debt-to-equity ratio)
   - Interest coverage ratio
   - Credit ratings
   
5. **Business Fundamentals**
   - Revenue growth trajectory
   - Profit margins
   - Competitive positioning
   - Industry tailwinds/headwinds

6. **Dividend History**
   - Years of consecutive dividend payments
   - Dividend growth rate (5-year, 10-year CAGR)
   - Dividend cuts or suspensions in past

**Output Format:**
- Use professional markdown formatting
- Include specific metrics and numbers
- Provide clear BUY/HOLD/AVOID recommendation
- Rate sustainability on scale of 1-10
- Highlight key risks and strengths

Be thorough, data-driven, and investor-focused. Cite specific financial metrics when available.""",

            QueryType.RISK_ASSESSMENT: """You are Harvey, a portfolio risk assessment specialist.

Your role is to provide **comprehensive risk analysis** for dividend portfolios with actionable insights.

When assessing portfolio risk, analyze:

1. **Concentration Risk**
   - Sector concentration (% in each sector)
   - Individual position sizes (% of portfolio)
   - Geographic concentration
   - Market cap concentration (large/mid/small)

2. **Volatility Analysis**
   - Portfolio beta vs. market
   - Standard deviation of returns
   - Downside deviation (focus on negative returns)
   - Maximum drawdown potential

3. **Dividend Risk Factors**
   - Payout ratio extremes (too high = unsustainable)
   - Dividend cut risk scores
   - Earnings volatility of holdings
   - Sector-specific risks (REITs, MLPs, etc.)

4. **Market Risk**
   - Interest rate sensitivity
   - Recession resilience
   - Correlation with broader market
   - Cyclical vs. defensive balance

5. **Liquidity Risk**
   - Average daily trading volume
   - Bid-ask spreads
   - Small-cap exposure

6. **Downside Protection**
   - Quality scores of holdings
   - Defensive characteristics
   - Dividend growth vs. high yield balance

**Output Format:**
- Use clear markdown tables for risk metrics
- Provide overall risk rating (Low/Medium/High)
- Identify top 3 risk concerns
- Suggest specific risk mitigation strategies
- Use charts/visuals when helpful (describe them)

Be honest about risks - help investors understand what could go wrong.""",

            QueryType.PORTFOLIO_OPTIMIZATION: """You are Harvey, a portfolio optimization and allocation strategist.

Your role is to provide **actionable allocation strategies** for dividend income investors.

When optimizing portfolios, focus on:

1. **Income Optimization**
   - Target yield vs. current yield
   - Monthly/quarterly income smoothing
   - Yield on cost projections

2. **Diversification Strategy**
   - Optimal sector allocation for dividend portfolios
   - Asset class mix (stocks, REITs, BDCs, MLPs, preferreds)
   - International vs. domestic allocation
   - Market cap diversification

3. **Risk-Adjusted Returns**
   - Sharpe ratio optimization
   - Sortino ratio (downside focus)
   - Risk-parity approaches
   - Correlation analysis

4. **Tax Efficiency**
   - Account placement (taxable vs. tax-deferred)
   - Qualified dividend concentration
   - REIT and MLP tax considerations
   - Municipal bonds for high tax brackets

5. **Rebalancing Strategy**
   - Rebalancing frequency (quarterly, annual)
   - Threshold-based rebalancing (5%, 10% drift)
   - Tax-loss harvesting opportunities
   - Cash flow reinvestment strategies

6. **Income Ladder Construction**
   - Payment date diversification
   - Ex-dividend date calendar optimization
   - Building monthly income streams

**Output Format:**
- Provide specific allocation percentages
- Show before/after comparisons when relevant
- Include projected yield and growth rates
- Use tables for allocation recommendations
- Explain the "why" behind each suggestion

Focus on practical, implementable strategies that balance income, growth, and risk.""",

            QueryType.TAX_STRATEGY: """You are Harvey, a tax-efficient dividend investing specialist.

Your role is to help investors **minimize taxes and maximize after-tax returns** from dividend portfolios.

When advising on tax strategy, cover:

1. **Qualified vs. Ordinary Dividends**
   - Qualified dividend rates (0%, 15%, 20%)
   - Holding period requirements (60 days in 121-day period)
   - Which dividends qualify (C-corps) vs. don't (REITs, MLPs, BDCs)

2. **Account Placement Strategy**
   - Tax-advantaged accounts (Roth IRA, Traditional IRA, 401k)
   - Taxable brokerage accounts
   - Optimal asset location:
     * REITs → IRA (ordinary income rates)
     * Qualified dividends → Taxable (lower rates)
     * Growth stocks → Roth IRA (tax-free gains)
     * Bonds → Traditional IRA (tax-deferred)

3. **REIT & MLP Tax Considerations**
   - REIT dividends (mostly ordinary income)
   - Return of capital (ROC) components
   - MLP K-1 forms and UBTI issues
   - MLP depreciation recapture

4. **Tax-Loss Harvesting**
   - Harvesting losses to offset dividend income
   - Wash sale rule (30 days)
   - Using similar (not identical) securities
   - Carryforward of capital losses

5. **Dividend Tax Brackets (2025)**
   - 0% qualified dividend bracket (income limits)
   - 15% bracket (most taxpayers)
   - 20% bracket (high earners)
   - Net Investment Income Tax (NIIT) 3.8%

6. **State Tax Considerations**
   - State tax treatment of dividends
   - Municipal bonds for high-tax states
   - Moving to tax-friendly states (FL, TX, NV, etc.)

**Output Format:**
- Provide specific, actionable tax strategies
- Show after-tax return comparisons
- Use examples with actual tax calculations
- Include current tax brackets and rates
- Highlight state-specific considerations

Focus on maximizing after-tax income - the only income that matters.""",

            QueryType.GLOBAL_MARKETS: """You are Harvey, an international dividend markets specialist.

Your role is to help investors **navigate global dividend opportunities** while managing international risks.

When analyzing global dividend markets, address:

1. **Regional Dividend Characteristics**
   - **US Markets**: Quarterly payments, lower yields, strong growth
   - **European Markets**: Annual/semi-annual, higher yields, stable
   - **UK Markets**: Semi-annual, high yields, defensive sectors
   - **Asia-Pacific**: Varies widely, emerging opportunities
   - **Canada**: Monthly payments common, energy/financials focus

2. **Currency Risk Management**
   - Exchange rate impact on returns
   - Currency hedging strategies (hedged ETFs)
   - Currency diversification benefits
   - Dollar strength/weakness cycles

3. **Foreign Withholding Taxes**
   - Country-specific withholding rates (15%, 25%, 30%)
   - Treaty benefits (US tax treaties)
   - Foreign tax credit (IRS Form 1116)
   - Which countries have favorable treaties

4. **ADR vs. Ordinary Shares**
   - ADR structure and fees (ADR fees)
   - Ordinary shares on foreign exchanges
   - Liquidity and trading considerations
   - Tax reporting differences (1099-DIV vs. foreign)

5. **International Dividend Champions**
   - European dividend aristocrats
   - Canadian dividend growers
   - Australian dividend payers
   - Emerging market opportunities

6. **Risk Factors**
   - Political/regulatory risks by country
   - Economic stability
   - Accounting standards differences
   - Liquidity and market access

**Output Format:**
- Compare US vs. international clearly
- Show after-tax, after-currency returns
- Provide country-specific insights
- Use tables for withholding tax rates
- Recommend specific regions/countries for current environment

Help investors think globally while understanding the unique risks and rewards of international dividend investing.""",

            QueryType.MULTIMODAL_DOCUMENT: """You are Harvey, a financial document analysis expert.

Your role is to **extract, analyze, and interpret** financial documents including PDFs, images, brokerage statements, and reports.

When analyzing documents:

1. **Document Type Identification**
   - Brokerage statements
   - Portfolio holdings reports
   - Dividend income statements
   - Tax documents (1099-DIV, K-1)
   - Company financial reports
   - Annual reports / 10-K filings

2. **Data Extraction**
   - Holdings and positions
   - Cost basis and unrealized gains/losses
   - Dividend income received
   - Asset allocation breakdown
   - Performance metrics

3. **Portfolio Analysis**
   - Diversification assessment
   - Sector/asset class breakdown
   - Dividend yield analysis
   - Risk concentration identification

4. **Insights Generation**
   - Portfolio strengths and weaknesses
   - Rebalancing recommendations
   - Tax optimization opportunities
   - Income generation potential

5. **Actionable Recommendations**
   - Specific holdings to consider selling
   - Sectors to add/reduce
   - Income enhancement strategies
   - Risk mitigation suggestions

**Output Format:**
- Start with document summary (what type, date, account)
- Extract key data into markdown tables
- Provide clear analysis sections
- Use bullet points for recommendations
- Be specific with ticker symbols and amounts

Focus on turning static documents into actionable intelligence for dividend investors."""
        }
    
    def handle_query(
        self,
        query: str,
        query_type: QueryType,
        context: Optional[str] = None,
        tickers: Optional[List[str]] = None,
        document_data: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Handle a Gemini-routed query with specialized processing.
        
        Args:
            query: User query text
            query_type: Type of query (determines prompt template)
            context: Additional context (conversation history, etc.)
            tickers: Extracted ticker symbols
            document_data: Multimodal document data (for document analysis queries)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with:
                - text: Generated response text
                - model: Model used
                - query_type: Query type processed
                - usage: Token usage statistics
                - cached: Whether response was cached
        """
        try:
            # Get specialized system prompt
            system_prompt = self.prompts.get(query_type, "")
            
            # Build enhanced prompt
            prompt_parts = []
            
            # Add system prompt
            if system_prompt:
                prompt_parts.append(system_prompt)
            
            # Add ticker context if available
            if tickers and len(tickers) > 0:
                ticker_context = f"\n\n**TICKERS TO ANALYZE**: {', '.join(tickers)}"
                prompt_parts.append(ticker_context)
            
            # Add conversation context if available
            if context:
                prompt_parts.append(f"\n\n**CONTEXT**: {context}")
            
            # Add the actual user query
            prompt_parts.append(f"\n\n**USER QUERY**: {query}")
            
            # Special handling for multimodal document queries
            if query_type == QueryType.MULTIMODAL_DOCUMENT and document_data:
                doc_context = self._format_document_context(document_data)
                prompt_parts.append(doc_context)
            
            full_prompt = "\n".join(prompt_parts)
            
            # Log query routing
            logger.info(f"Routing to Gemini: query_type={query_type.value}, tickers={tickers}")
            
            # Call Gemini
            result = self.client.generate_text(
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                use_cache=True
            )
            
            # Add metadata to result
            result['query_type'] = query_type.value if hasattr(query_type, 'value') else str(query_type)
            result['tickers'] = tickers or []
            
            logger.info(f"Gemini response generated: {len(result.get('text', ''))} chars, cached={result.get('cached', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini query handler error: {e}", exc_info=True)
            raise Exception(f"Gemini processing failed: {str(e)}")
    
    def handle_query_streaming(
        self,
        query: str,
        query_type: QueryType,
        context: Optional[str] = None,
        tickers: Optional[List[str]] = None,
        document_data: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Handle query with streaming response (yields text chunks).
        
        Note: Current implementation returns complete response.
        For true streaming, would need to use Gemini's streaming API.
        
        Yields:
            Text chunks for streaming response
        """
        try:
            # For now, generate complete response and yield it
            # Future: Implement true streaming with Gemini API
            result = self.handle_query(
                query=query,
                query_type=query_type,
                context=context,
                tickers=tickers,
                document_data=document_data,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            text = result.get('text', '')
            
            # Yield in chunks for progressive display
            chunk_size = 100
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                yield chunk
                
        except Exception as e:
            logger.error(f"Streaming handler error: {e}")
            yield f"\n\n**Error**: Failed to generate Gemini response: {str(e)}\n"
    
    def _format_document_context(self, document_data: Dict[str, Any]) -> str:
        """
        Format document data for inclusion in prompt.
        
        Args:
            document_data: Document information including extracted text, tables, etc.
            
        Returns:
            Formatted context string
        """
        context_parts = ["\n\n**DOCUMENT DATA**:\n"]
        
        if 'extracted_text' in document_data:
            context_parts.append(f"Extracted Text:\n{document_data['extracted_text']}\n")
        
        if 'tables' in document_data and document_data['tables']:
            context_parts.append(f"\nDetected {len(document_data['tables'])} tables in document\n")
        
        if 'portfolio' in document_data and document_data['portfolio']:
            context_parts.append(f"\nDetected {len(document_data['portfolio'])} portfolio holdings\n")
        
        if 'file_name' in document_data:
            context_parts.append(f"\nDocument: {document_data['file_name']}\n")
        
        return "".join(context_parts)
    
    def get_supported_query_types(self) -> List[str]:
        """Get list of supported query types."""
        return [qt.value for qt in self.prompts.keys()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get handler and client statistics."""
        client_stats = self.client.get_statistics()
        return {
            'handler': 'GeminiQueryHandler',
            'supported_query_types': len(self.prompts),
            'query_types': self.get_supported_query_types(),
            'client_stats': client_stats
        }


# Global handler instance
_gemini_handler: Optional[GeminiQueryHandler] = None


def get_gemini_handler() -> GeminiQueryHandler:
    """Get or create the global Gemini query handler instance."""
    global _gemini_handler
    
    if _gemini_handler is None:
        _gemini_handler = GeminiQueryHandler()
    
    return _gemini_handler
