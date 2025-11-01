"""
PDF.co Integration Service for Advanced PDF Processing

Provides enterprise-grade PDF processing capabilities including:
- Advanced OCR with table extraction
- PDF to Excel/CSV conversion for financial data
- Multi-page document processing
- Form filling and data extraction
- Structured data extraction from financial statements

Complements the existing Node service with specialized PDF capabilities.
"""

import os
import time
import logging
import requests
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.config.settings import PDFCO_API_KEY, PDFCO_API_ENABLED

logger = logging.getLogger("pdfco_service")

PDFCO_BASE_URL = "https://api.pdf.co/v1"


class PDFCoError(Exception):
    """Base exception for PDF.co service errors"""
    pass


class ExtractionFormat(Enum):
    """Output formats for data extraction"""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    HTML = "html"


@dataclass
class ExtractionResult:
    """Result from PDF.co extraction"""
    success: bool
    text: str = ""
    tables: Optional[List[Dict[str, Any]]] = None
    structured_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: int = 0
    page_count: int = 0
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = []
        if self.structured_data is None:
            self.structured_data = {}


class PDFCoService:
    """
    PDF.co API integration for advanced PDF processing.
    
    Features:
    - OCR with table extraction
    - PDF to Excel/CSV conversion
    - Multi-page processing
    - Financial document parsing
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or PDFCO_API_KEY
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("PDF.co service disabled: PDFCO_API_KEY not set")
    
    def _make_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """Make authenticated request to PDF.co API"""
        if not self.enabled:
            raise PDFCoError("PDF.co service not enabled: API key missing")
        
        url = f"{PDFCO_BASE_URL}/{endpoint}"
        headers = {"x-api-key": self.api_key}
        
        try:
            if method == "POST":
                if files:
                    response = requests.post(url, headers=headers, data=data, files=files, timeout=timeout)
                else:
                    headers["Content-Type"] = "application/json"
                    response = requests.post(url, headers=headers, json=data, timeout=timeout)
            else:
                response = requests.get(url, headers=headers, params=data, timeout=timeout)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            raise PDFCoError(f"PDF.co API timeout after {timeout}s")
        except requests.exceptions.RequestException as e:
            raise PDFCoError(f"PDF.co API request failed: {str(e)}")
    
    def extract_text_from_pdf(
        self,
        file_bytes: bytes,
        file_name: str = "document.pdf",
        extract_tables: bool = True,
        ocr_enabled: bool = True,
        rid: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract text and tables from PDF using advanced OCR.
        
        Args:
            file_bytes: PDF file content as bytes
            file_name: Original filename for logging
            extract_tables: Whether to extract tables
            ocr_enabled: Whether to use OCR for scanned documents
            rid: Request ID for logging
        
        Returns:
            ExtractionResult with text, tables, and metadata
        """
        tag = f"[{rid}]" if rid else "[pdfco]"
        
        if not self.enabled:
            logger.warning(f"{tag} PDF.co service disabled, returning empty result")
            return ExtractionResult(success=False, error="PDF.co API key not configured")
        
        try:
            start_time = time.time()
            logger.info(f"{tag} Starting PDF.co extraction: file={file_name}, size={len(file_bytes)}, tables={extract_tables}, ocr={ocr_enabled}")
            
            files = {"file": (file_name, file_bytes, "application/pdf")}
            data = {
                "async": False,
                "inline": True,
                "ocr": ocr_enabled,
                "extractTables": extract_tables
            }
            
            result = self._make_request(
                endpoint="pdf/convert/to/json",
                method="POST",
                data=data,
                files=files,
                timeout=120
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            if not result.get("error"):
                text_content = result.get("text", "")
                tables = result.get("tables", [])
                pages = result.get("pages", [])
                
                logger.info(f"{tag} PDF.co extraction successful: {len(text_content)} chars, {len(tables)} tables, {len(pages)} pages, {elapsed_ms}ms")
                
                return ExtractionResult(
                    success=True,
                    text=text_content,
                    tables=tables,
                    structured_data={
                        "pages": pages,
                        "metadata": result.get("metadata", {})
                    },
                    processing_time_ms=elapsed_ms,
                    page_count=len(pages)
                )
            else:
                error_msg = result.get("message", "Unknown PDF.co error")
                logger.error(f"{tag} PDF.co extraction failed: {error_msg}")
                return ExtractionResult(success=False, error=error_msg, processing_time_ms=elapsed_ms)
        
        except PDFCoError as e:
            logger.exception(f"{tag} PDF.co service error: {e}")
            return ExtractionResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"{tag} Unexpected error in PDF.co extraction: {e}")
            return ExtractionResult(success=False, error=f"Unexpected error: {str(e)}")
    
    def pdf_to_excel(
        self,
        file_bytes: bytes,
        file_name: str = "document.pdf",
        extract_all_pages: bool = True,
        rid: Optional[str] = None
    ) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Convert PDF to Excel format (ideal for financial tables).
        
        Args:
            file_bytes: PDF file content
            file_name: Original filename
            extract_all_pages: Whether to extract all pages or just first page
            rid: Request ID for logging
        
        Returns:
            Tuple of (success, excel_bytes, error_message)
        """
        tag = f"[{rid}]" if rid else "[pdfco]"
        
        if not self.enabled:
            return False, None, "PDF.co API key not configured"
        
        try:
            logger.info(f"{tag} Converting PDF to Excel: file={file_name}, all_pages={extract_all_pages}")
            
            files = {"file": (file_name, file_bytes, "application/pdf")}
            data = {
                "async": False,
                "pages": "" if extract_all_pages else "0",
                "unwrap": True
            }
            
            result = self._make_request(
                endpoint="pdf/convert/to/xls",
                method="POST",
                data=data,
                files=files,
                timeout=120
            )
            
            if not result.get("error"):
                excel_url = result.get("url")
                if excel_url:
                    excel_response = requests.get(excel_url, timeout=30)
                    excel_response.raise_for_status()
                    excel_bytes = excel_response.content
                    logger.info(f"{tag} Excel conversion successful: {len(excel_bytes)} bytes")
                    return True, excel_bytes, None
                else:
                    return False, None, "No Excel URL in response"
            else:
                error_msg = result.get("message", "Excel conversion failed")
                logger.error(f"{tag} Excel conversion failed: {error_msg}")
                return False, None, error_msg
        
        except Exception as e:
            logger.exception(f"{tag} Excel conversion error: {e}")
            return False, None, str(e)
    
    def pdf_to_csv(
        self,
        file_bytes: bytes,
        file_name: str = "document.pdf",
        page_index: int = 0,
        rid: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convert PDF page to CSV format (ideal for financial tables).
        
        Args:
            file_bytes: PDF file content
            file_name: Original filename
            page_index: Page number to extract (0-indexed)
            rid: Request ID for logging
        
        Returns:
            Tuple of (success, csv_text, error_message)
        """
        tag = f"[{rid}]" if rid else "[pdfco]"
        
        if not self.enabled:
            return False, None, "PDF.co API key not configured"
        
        try:
            logger.info(f"{tag} Converting PDF to CSV: file={file_name}, page={page_index}")
            
            files = {"file": (file_name, file_bytes, "application/pdf")}
            data = {
                "async": False,
                "pages": str(page_index)
            }
            
            result = self._make_request(
                endpoint="pdf/convert/to/csv",
                method="POST",
                data=data,
                files=files,
                timeout=120
            )
            
            if not result.get("error"):
                csv_url = result.get("url")
                if csv_url:
                    csv_response = requests.get(csv_url, timeout=30)
                    csv_response.raise_for_status()
                    csv_text = csv_response.text
                    logger.info(f"{tag} CSV conversion successful: {len(csv_text)} chars")
                    return True, csv_text, None
                else:
                    return False, None, "No CSV URL in response"
            else:
                error_msg = result.get("message", "CSV conversion failed")
                logger.error(f"{tag} CSV conversion failed: {error_msg}")
                return False, None, error_msg
        
        except Exception as e:
            logger.exception(f"{tag} CSV conversion error: {e}")
            return False, None, str(e)
    
    def extract_tables_from_pdf(
        self,
        file_bytes: bytes,
        file_name: str = "document.pdf",
        page_numbers: Optional[List[int]] = None,
        rid: Optional[str] = None
    ) -> Tuple[bool, List[List[List[str]]], Optional[str]]:
        """
        Extract all tables from PDF as structured data.
        
        Args:
            file_bytes: PDF file content
            file_name: Original filename
            page_numbers: Specific pages to extract (None = all pages)
            rid: Request ID for logging
        
        Returns:
            Tuple of (success, tables_list, error_message)
            tables_list is a list of tables, where each table is a 2D list of cells
        """
        tag = f"[{rid}]" if rid else "[pdfco]"
        
        if not self.enabled:
            return False, [], "PDF.co API key not configured"
        
        try:
            pages_param = ",".join(map(str, page_numbers)) if page_numbers else ""
            logger.info(f"{tag} Extracting tables from PDF: file={file_name}, pages={pages_param or 'all'}")
            
            files = {"file": (file_name, file_bytes, "application/pdf")}
            data = {
                "async": False,
                "pages": pages_param
            }
            
            result = self._make_request(
                endpoint="pdf/convert/to/json",
                method="POST",
                data=data,
                files=files,
                timeout=120
            )
            
            if not result.get("error"):
                tables = result.get("tables", [])
                extracted_tables = []
                
                for table in tables:
                    rows = table.get("rows", [])
                    table_data = []
                    for row in rows:
                        cells = row.get("cells", [])
                        cell_values = [cell.get("text", "") for cell in cells]
                        table_data.append(cell_values)
                    extracted_tables.append(table_data)
                
                logger.info(f"{tag} Table extraction successful: {len(extracted_tables)} tables found")
                return True, extracted_tables, None
            else:
                error_msg = result.get("message", "Table extraction failed")
                logger.error(f"{tag} Table extraction failed: {error_msg}")
                return False, [], error_msg
        
        except Exception as e:
            logger.exception(f"{tag} Table extraction error: {e}")
            return False, [], str(e)
    
    def extract_financial_data(
        self,
        file_bytes: bytes,
        file_name: str = "statement.pdf",
        rid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Specialized extraction for financial documents (statements, reports).
        
        Attempts to extract:
        - Portfolio holdings (tickers, shares, values)
        - Dividend payments
        - Account balances
        - Transaction history
        
        Args:
            file_bytes: PDF file content
            file_name: Original filename
            rid: Request ID for logging
        
        Returns:
            Dict with extracted financial data
        """
        tag = f"[{rid}]" if rid else "[pdfco]"
        
        logger.info(f"{tag} Extracting financial data from: {file_name}")
        
        extraction_result = self.extract_text_from_pdf(
            file_bytes=file_bytes,
            file_name=file_name,
            extract_tables=True,
            ocr_enabled=True,
            rid=rid
        )
        
        if not extraction_result.success:
            return {
                "success": False,
                "error": extraction_result.error,
                "extracted_text": "",
                "tables": [],
                "portfolio": [],
                "dividends": []
            }
        
        return {
            "success": True,
            "extracted_text": extraction_result.text,
            "tables": extraction_result.tables,
            "page_count": extraction_result.page_count,
            "processing_time_ms": extraction_result.processing_time_ms,
            "portfolio": self._parse_portfolio_data(extraction_result),
            "dividends": self._parse_dividend_data(extraction_result),
            "metadata": extraction_result.structured_data.get("metadata", {})
        }
    
    def _parse_portfolio_data(self, extraction_result: ExtractionResult) -> List[Dict[str, Any]]:
        """
        Parse portfolio holdings from extracted text and tables.
        
        Looks for patterns like:
        - AAPL  100  $15,000
        - MSFT  50   $12,500
        """
        portfolio = []
        
        import re
        ticker_pattern = r'\b([A-Z]{1,5})\b'
        
        for table in extraction_result.tables:
            rows = table.get("rows", [])
            for row in rows:
                cells = row.get("cells", [])
                if len(cells) >= 2:
                    cell_texts = [cell.get("text", "").strip() for cell in cells]
                    
                    for i, text in enumerate(cell_texts):
                        ticker_match = re.match(r'^([A-Z]{1,5})$', text)
                        if ticker_match and i + 1 < len(cell_texts):
                            ticker = ticker_match.group(1)
                            shares_text = cell_texts[i + 1]
                            
                            try:
                                shares = float(shares_text.replace(",", ""))
                                portfolio.append({
                                    "ticker": ticker,
                                    "shares": shares,
                                    "source": "table_extraction"
                                })
                            except ValueError:
                                pass
        
        return portfolio
    
    def _parse_dividend_data(self, extraction_result: ExtractionResult) -> List[Dict[str, Any]]:
        """Parse dividend information from extracted text"""
        dividends = []
        
        import re
        text = extraction_result.text.lower()
        
        if "dividend" in text or "distribution" in text:
            dividend_pattern = r'([A-Z]{1,5})\s+\$?([\d,]+\.?\d*)'
            matches = re.findall(dividend_pattern, extraction_result.text)
            
            for ticker, amount in matches:
                try:
                    amount_float = float(amount.replace(",", ""))
                    dividends.append({
                        "ticker": ticker,
                        "amount": amount_float,
                        "source": "text_extraction"
                    })
                except ValueError:
                    pass
        
        return dividends
    
    def health_check(self) -> Dict[str, Any]:
        """Check if PDF.co service is available and working"""
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "PDF.co API key not configured",
                "enabled": False
            }
        
        try:
            result = self._make_request(
                endpoint="pdf/info",
                method="GET",
                timeout=10
            )
            
            return {
                "status": "healthy",
                "message": "PDF.co service operational",
                "enabled": True,
                "credits_remaining": result.get("remainingCredits"),
                "api_version": result.get("version")
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "enabled": True
            }


pdfco_service = PDFCoService()
