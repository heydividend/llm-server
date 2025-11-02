"""
Azure Document Intelligence Integration
Replaces PDF.co for document processing with native Azure integration.

Features:
- Advanced OCR with table extraction
- Layout analysis and document structure detection
- Multi-page document processing
- Financial document parsing (invoices, statements, receipts)
- Support for PDF, images, Office documents
- Built-in models for common document types

Cost Advantages:
- Native Azure integration (same infrastructure as Harvey)
- Lower cost vs. third-party API (PDF.co)
- No data egress charges within Azure
- Generous free tier: 500 pages/month
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from io import BytesIO

logger = logging.getLogger("azure_document_intelligence")

# Azure Document Intelligence configuration
AZURE_DI_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
AZURE_DI_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
AZURE_DI_ENABLED = bool(AZURE_DI_ENDPOINT and AZURE_DI_KEY)


class DocumentIntelligenceError(Exception):
    """Base exception for Azure Document Intelligence errors"""
    pass


class ExtractionFormat(Enum):
    """Output formats for data extraction"""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"


@dataclass
class ExtractionResult:
    """Result from Azure Document Intelligence extraction"""
    success: bool
    text: str = ""
    tables: Optional[List[Dict[str, Any]]] = None
    structured_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: int = 0
    page_count: int = 0
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = []
        if self.structured_data is None:
            self.structured_data = {}


class AzureDocumentIntelligence:
    """
    Azure Document Intelligence API integration for document processing.
    
    Provides enterprise-grade document understanding with:
    - Layout analysis
    - Table extraction
    - Key-value pair extraction
    - Financial document models
    """
    
    def __init__(self, endpoint: Optional[str] = None, key: Optional[str] = None):
        self.endpoint = endpoint or AZURE_DI_ENDPOINT
        self.key = key or AZURE_DI_KEY
        self.enabled = bool(self.endpoint and self.key)
        
        if not self.enabled:
            logger.warning(
                "Azure Document Intelligence disabled: "
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT or AZURE_DOCUMENT_INTELLIGENCE_KEY not set"
            )
        else:
            # Lazy import to avoid errors when package not installed
            try:
                from azure.ai.documentintelligence import DocumentIntelligenceClient
                from azure.core.credentials import AzureKeyCredential
                
                self.client = DocumentIntelligenceClient(
                    endpoint=self.endpoint,
                    credential=AzureKeyCredential(self.key)
                )
                logger.info(f"✅ Azure Document Intelligence initialized: {self.endpoint}")
            except ImportError:
                logger.error(
                    "azure-ai-documentintelligence package not installed. "
                    "Run: pip install azure-ai-documentintelligence"
                )
                self.enabled = False
                self.client = None
    
    def extract_text_from_pdf(
        self,
        file_bytes: bytes,
        file_name: str = "document.pdf",
        extract_tables: bool = True,
        extract_key_values: bool = True,
        rid: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract text and tables from PDF using Azure Document Intelligence.
        
        Args:
            file_bytes: PDF file content as bytes
            file_name: Original filename for logging
            extract_tables: Whether to extract tables
            extract_key_values: Whether to extract key-value pairs
            rid: Request ID for logging
            
        Returns:
            ExtractionResult with extracted content
        """
        if not self.enabled or not self.client:
            return ExtractionResult(
                success=False,
                error="Azure Document Intelligence not enabled"
            )
        
        start_time = time.time()
        log_prefix = f"[{rid}]" if rid else ""
        
        try:
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
            
            logger.info(f"{log_prefix} Analyzing document with Azure DI: {file_name}")
            
            # Use prebuilt-layout model for general document analysis
            # This model extracts text, tables, and document structure
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout",
                analyze_request=AnalyzeDocumentRequest(bytes_source=file_bytes),
                content_type="application/octet-stream"
            )
            
            result = poller.result()
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract text content
            full_text = result.content if result.content else ""
            
            # Extract tables
            tables = []
            if extract_tables and result.tables:
                for table in result.tables:
                    table_data = {
                        "row_count": table.row_count,
                        "column_count": table.column_count,
                        "cells": []
                    }
                    
                    for cell in table.cells:
                        table_data["cells"].append({
                            "content": cell.content,
                            "row_index": cell.row_index,
                            "column_index": cell.column_index,
                            "row_span": getattr(cell, "row_span", 1),
                            "column_span": getattr(cell, "column_span", 1),
                            "confidence": getattr(cell, "confidence", 1.0)
                        })
                    
                    tables.append(table_data)
            
            # Extract key-value pairs
            structured_data = {}
            if extract_key_values and result.key_value_pairs:
                for kv in result.key_value_pairs:
                    if kv.key and kv.value:
                        key_text = kv.key.content if hasattr(kv.key, "content") else str(kv.key)
                        value_text = kv.value.content if hasattr(kv.value, "content") else str(kv.value)
                        structured_data[key_text] = value_text
            
            # Calculate average confidence
            avg_confidence = 0.0
            if result.pages:
                confidence_scores = []
                for page in result.pages:
                    if hasattr(page, "confidence"):
                        confidence_scores.append(page.confidence)
                if confidence_scores:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            logger.info(
                f"{log_prefix} Azure DI extraction completed: "
                f"{len(result.pages)} pages, {len(tables)} tables, "
                f"{len(structured_data)} key-value pairs in {processing_time_ms}ms"
            )
            
            return ExtractionResult(
                success=True,
                text=full_text,
                tables=tables,
                structured_data=structured_data,
                processing_time_ms=processing_time_ms,
                page_count=len(result.pages) if result.pages else 0,
                confidence=avg_confidence
            )
        
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Azure Document Intelligence extraction failed: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            
            return ExtractionResult(
                success=False,
                error=error_msg,
                processing_time_ms=processing_time_ms
            )
    
    def extract_from_image(
        self,
        image_bytes: bytes,
        file_name: str = "image.jpg",
        extract_tables: bool = True,
        rid: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract text from image using Azure Document Intelligence OCR.
        
        Works with: JPG, PNG, BMP, TIFF
        """
        return self.extract_text_from_pdf(
            image_bytes,
            file_name,
            extract_tables=extract_tables,
            rid=rid
        )
    
    def analyze_financial_document(
        self,
        file_bytes: bytes,
        document_type: str = "invoice",
        rid: Optional[str] = None
    ) -> ExtractionResult:
        """
        Analyze financial documents using specialized models.
        
        Supported types:
        - invoice: Extract invoice data (amounts, dates, vendors)
        - receipt: Extract receipt information
        - w2: Extract W-2 tax form data
        - 1099: Extract 1099 form data
        
        Args:
            file_bytes: Document file bytes
            document_type: Type of financial document
            rid: Request ID for logging
        """
        if not self.enabled or not self.client:
            return ExtractionResult(
                success=False,
                error="Azure Document Intelligence not enabled"
            )
        
        start_time = time.time()
        log_prefix = f"[{rid}]" if rid else ""
        
        # Map document types to Azure prebuilt models
        model_map = {
            "invoice": "prebuilt-invoice",
            "receipt": "prebuilt-receipt",
            "w2": "prebuilt-tax.us.w2",
            "1099": "prebuilt-tax.us.1099"
        }
        
        model_id = model_map.get(document_type.lower(), "prebuilt-document")
        
        try:
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
            
            logger.info(f"{log_prefix} Analyzing {document_type} with model: {model_id}")
            
            poller = self.client.begin_analyze_document(
                model_id=model_id,
                analyze_request=AnalyzeDocumentRequest(bytes_source=file_bytes),
                content_type="application/octet-stream"
            )
            
            result = poller.result()
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract structured fields from financial document
            structured_data = {}
            if result.documents:
                for doc in result.documents:
                    if doc.fields:
                        for field_name, field_value in doc.fields.items():
                            if field_value:
                                structured_data[field_name] = {
                                    "value": field_value.value_string if hasattr(field_value, "value_string") else str(field_value.value),
                                    "confidence": field_value.confidence if hasattr(field_value, "confidence") else 1.0
                                }
            
            full_text = result.content if result.content else ""
            
            logger.info(
                f"{log_prefix} Financial document analysis completed: "
                f"{len(structured_data)} fields extracted in {processing_time_ms}ms"
            )
            
            return ExtractionResult(
                success=True,
                text=full_text,
                structured_data=structured_data,
                processing_time_ms=processing_time_ms,
                page_count=len(result.pages) if result.pages else 0
            )
        
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Financial document analysis failed: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            
            return ExtractionResult(
                success=False,
                error=error_msg,
                processing_time_ms=processing_time_ms
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health and configuration"""
        return {
            "enabled": self.enabled,
            "endpoint": self.endpoint if self.enabled else None,
            "has_client": self.client is not None,
            "status": "healthy" if self.enabled and self.client else "disabled"
        }


# Global service instance
azure_di_service = AzureDocumentIntelligence()


# Compatibility wrapper for PDF.co replacement
def extract_text_from_pdf(file_bytes: bytes, file_name: str = "document.pdf", **kwargs) -> ExtractionResult:
    """
    Drop-in replacement for pdfco_service.extract_text_from_pdf
    Routes to Azure Document Intelligence when available
    """
    return azure_di_service.extract_text_from_pdf(file_bytes, file_name, **kwargs)
