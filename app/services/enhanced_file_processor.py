"""
Enhanced File Processing Service

Unified file processing for Harvey supporting:
- Local files: PDF, CSV, JPG, PNG, JPEG, XLS, XLSX
- Cloud sources: Google Sheets, Google Drive, OneDrive
- Automatic format detection and conversion
- Portfolio data extraction
"""

import os
import io
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("enhanced_file_processor")


class FileSource(Enum):
    """File source types"""
    LOCAL = "local"
    GOOGLE_SHEETS = "google_sheets"
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"


class FileType(Enum):
    """Supported file types"""
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    JPG = "jpg"
    PNG = "png"
    JPEG = "jpeg"
    UNKNOWN = "unknown"


@dataclass
class ProcessedFile:
    """Result from file processing"""
    success: bool
    file_type: FileType
    source: FileSource
    extracted_text: str = ""
    portfolio_holdings: list = None
    tables: list = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.portfolio_holdings is None:
            self.portfolio_holdings = []
        if self.tables is None:
            self.tables = []
        if self.metadata is None:
            self.metadata = {}


class EnhancedFileProcessor:
    """
    Unified file processor for all supported formats and sources.
    """
    
    def __init__(self):
        # Import services
        from app.services.azure_document_intelligence import azure_di_service
        from app.services.portfolio_parser import portfolio_parser
        from app.services.google_sheets_service import google_sheets_service
        from app.services.google_drive_service import google_drive_service
        from app.services.onedrive_service import onedrive_service
        
        self.azure_di = azure_di_service
        self.portfolio_parser = portfolio_parser
        self.google_sheets = google_sheets_service
        self.google_drive = google_drive_service
        self.onedrive = onedrive_service
        
        logger.info("✅ Enhanced File Processor initialized")
    
    def detect_file_type(self, file_name: str, file_bytes: bytes = None) -> FileType:
        """Detect file type from filename and content"""
        file_name = file_name.lower()
        
        if file_name.endswith('.pdf'):
            return FileType.PDF
        elif file_name.endswith('.csv'):
            return FileType.CSV
        elif file_name.endswith('.xlsx'):
            return FileType.XLSX
        elif file_name.endswith('.xls'):
            return FileType.XLS
        elif file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
            return FileType.JPG
        elif file_name.endswith('.png'):
            return FileType.PNG
        
        # Try to detect from content if available
        if file_bytes:
            if file_bytes.startswith(b'%PDF'):
                return FileType.PDF
            elif file_bytes.startswith(b'PK'):  # ZIP-based formats (XLSX)
                return FileType.XLSX
            elif file_bytes.startswith(b'\x89PNG'):
                return FileType.PNG
            elif file_bytes.startswith(b'\xFF\xD8\xFF'):
                return FileType.JPG
        
        return FileType.UNKNOWN
    
    def detect_source(self, url_or_path: str) -> FileSource:
        """Detect file source from URL or path"""
        url = url_or_path.lower()
        
        if 'docs.google.com/spreadsheets' in url:
            return FileSource.GOOGLE_SHEETS
        elif 'drive.google.com' in url or '1drv.ms' in url:
            if 'google' in url:
                return FileSource.GOOGLE_DRIVE
            else:
                return FileSource.ONEDRIVE
        elif 'onedrive.live.com' in url or 'sharepoint.com' in url:
            return FileSource.ONEDRIVE
        
        return FileSource.LOCAL
    
    def process_excel_file(
        self,
        file_bytes: bytes,
        file_name: str,
        file_type: FileType,
        rid: Optional[str] = None
    ) -> ProcessedFile:
        """Process Excel files (XLS, XLSX) using pandas"""
        log_prefix = f"[{rid}]" if rid else ""
        
        try:
            import pandas as pd
            
            logger.info(f"{log_prefix} Processing Excel file: {file_name} ({file_type.value})")
            
            # Read Excel file
            if file_type == FileType.XLSX:
                df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
            else:  # XLS
                df = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
            
            # Convert to CSV text for portfolio parser
            csv_text = df.to_csv(index=False)
            
            # Parse portfolio holdings
            holdings = self.portfolio_parser.parse_csv_text(csv_text, rid)
            
            # Extract text representation
            text = f"Excel file: {file_name}\n"
            text += f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
            text += f"Columns: {', '.join(df.columns)}\n\n"
            text += csv_text
            
            logger.info(
                f"{log_prefix} Excel processing complete: "
                f"{len(df)} rows, {len(holdings)} holdings detected"
            )
            
            return ProcessedFile(
                success=True,
                file_type=file_type,
                source=FileSource.LOCAL,
                extracted_text=text,
                portfolio_holdings=holdings,
                metadata={
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns)
                }
            )
        
        except Exception as e:
            error_msg = f"Excel processing failed: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            return ProcessedFile(
                success=False,
                file_type=file_type,
                source=FileSource.LOCAL,
                error=error_msg
            )
    
    def process_csv_file(
        self,
        file_bytes: bytes,
        file_name: str,
        rid: Optional[str] = None
    ) -> ProcessedFile:
        """Process CSV files"""
        log_prefix = f"[{rid}]" if rid else ""
        
        try:
            # Decode CSV content
            csv_text = file_bytes.decode('utf-8')
            
            logger.info(f"{log_prefix} Processing CSV file: {file_name}")
            
            # Parse portfolio holdings
            holdings = self.portfolio_parser.parse_csv_text(csv_text, rid)
            
            logger.info(f"{log_prefix} CSV processing complete: {len(holdings)} holdings detected")
            
            return ProcessedFile(
                success=True,
                file_type=FileType.CSV,
                source=FileSource.LOCAL,
                extracted_text=csv_text,
                portfolio_holdings=holdings
            )
        
        except Exception as e:
            error_msg = f"CSV processing failed: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            return ProcessedFile(
                success=False,
                file_type=FileType.CSV,
                source=FileSource.LOCAL,
                error=error_msg
            )
    
    def process_pdf_or_image(
        self,
        file_bytes: bytes,
        file_name: str,
        file_type: FileType,
        rid: Optional[str] = None
    ) -> ProcessedFile:
        """Process PDF or image files using Azure Document Intelligence"""
        log_prefix = f"[{rid}]" if rid else ""
        
        logger.info(f"{log_prefix} Processing {file_type.value} file: {file_name}")
        
        # Use Azure Document Intelligence for OCR and table extraction
        if file_type == FileType.PDF:
            result = self.azure_di.extract_text_from_pdf(file_bytes, file_name, rid=rid)
        else:
            result = self.azure_di.extract_from_image(file_bytes, file_name, rid=rid)
        
        if not result.success:
            return ProcessedFile(
                success=False,
                file_type=file_type,
                source=FileSource.LOCAL,
                error=result.error
            )
        
        # Parse portfolio holdings from extracted text
        holdings = self.portfolio_parser.parse_extracted_text(result.text, rid)
        
        logger.info(
            f"{log_prefix} {file_type.value.upper()} processing complete: "
            f"{len(holdings)} holdings detected"
        )
        
        return ProcessedFile(
            success=True,
            file_type=file_type,
            source=FileSource.LOCAL,
            extracted_text=result.text,
            portfolio_holdings=holdings,
            tables=result.tables,
            metadata={
                "page_count": result.page_count,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms
            }
        )
    
    def process_local_file(
        self,
        file_bytes: bytes,
        file_name: str,
        rid: Optional[str] = None
    ) -> ProcessedFile:
        """Process a local uploaded file"""
        # Detect file type
        file_type = self.detect_file_type(file_name, file_bytes)
        
        if file_type == FileType.UNKNOWN:
            return ProcessedFile(
                success=False,
                file_type=file_type,
                source=FileSource.LOCAL,
                error=f"Unsupported file type: {file_name}"
            )
        
        # Route to appropriate processor
        if file_type in [FileType.XLS, FileType.XLSX]:
            return self.process_excel_file(file_bytes, file_name, file_type, rid)
        elif file_type == FileType.CSV:
            return self.process_csv_file(file_bytes, file_name, rid)
        elif file_type in [FileType.PDF, FileType.JPG, FileType.PNG, FileType.JPEG]:
            return self.process_pdf_or_image(file_bytes, file_name, file_type, rid)
        else:
            return ProcessedFile(
                success=False,
                file_type=file_type,
                source=FileSource.LOCAL,
                error=f"Unsupported file type: {file_type.value}"
            )
    
    def process_google_sheets(
        self,
        sheets_url: str,
        rid: Optional[str] = None
    ) -> ProcessedFile:
        """Process a Google Sheets URL"""
        log_prefix = f"[{rid}]" if rid else ""
        
        logger.info(f"{log_prefix} Processing Google Sheets: {sheets_url}")
        
        # Read from Google Sheets
        sheets_data = self.google_sheets.read_sheet(sheets_url, rid=rid)
        
        if not sheets_data.success:
            return ProcessedFile(
                success=False,
                file_type=FileType.CSV,
                source=FileSource.GOOGLE_SHEETS,
                error=sheets_data.error
            )
        
        # Convert to CSV and parse
        csv_text = self.google_sheets.convert_to_csv(sheets_data)
        holdings = self.portfolio_parser.parse_csv_text(csv_text, rid)
        
        logger.info(
            f"{log_prefix} Google Sheets processing complete: {len(holdings)} holdings detected"
        )
        
        return ProcessedFile(
            success=True,
            file_type=FileType.CSV,
            source=FileSource.GOOGLE_SHEETS,
            extracted_text=csv_text,
            portfolio_holdings=holdings,
            metadata={
                "sheet_name": sheets_data.sheet_name,
                "row_count": len(sheets_data.data),
                "column_count": len(sheets_data.headers)
            }
        )
    
    def process_google_drive(
        self,
        drive_url: str,
        rid: Optional[str] = None
    ) -> ProcessedFile:
        """Process a Google Drive file URL"""
        log_prefix = f"[{rid}]" if rid else ""
        
        logger.info(f"{log_prefix} Processing Google Drive file: {drive_url}")
        
        # Download from Google Drive
        file_data = self.google_drive.download_file(drive_url, rid=rid)
        
        if not file_data.success:
            return ProcessedFile(
                success=False,
                file_type=FileType.UNKNOWN,
                source=FileSource.GOOGLE_DRIVE,
                error=file_data.error
            )
        
        # Process the downloaded file
        result = self.process_local_file(file_data.file_bytes, file_data.file_name, rid)
        result.source = FileSource.GOOGLE_DRIVE
        result.metadata = result.metadata or {}
        result.metadata["original_url"] = drive_url
        
        return result
    
    def process_onedrive(
        self,
        onedrive_url: str,
        rid: Optional[str] = None
    ) -> ProcessedFile:
        """Process a OneDrive file URL"""
        log_prefix = f"[{rid}]" if rid else ""
        
        logger.info(f"{log_prefix} Processing OneDrive file: {onedrive_url}")
        
        # Download from OneDrive
        file_data = self.onedrive.download_file(onedrive_url, rid=rid)
        
        if not file_data.success:
            return ProcessedFile(
                success=False,
                file_type=FileType.UNKNOWN,
                source=FileSource.ONEDRIVE,
                error=file_data.error
            )
        
        # Process the downloaded file
        result = self.process_local_file(file_data.file_bytes, file_data.file_name, rid)
        result.source = FileSource.ONEDRIVE
        result.metadata = result.metadata or {}
        result.metadata["original_url"] = onedrive_url
        
        return result
    
    def process_file(
        self,
        file_bytes: bytes = None,
        file_name: str = None,
        url: str = None,
        rid: Optional[str] = None
    ) -> ProcessedFile:
        """
        Unified file processing entry point.
        
        Args:
            file_bytes: File content (for local uploads)
            file_name: File name (for local uploads)
            url: Cloud file URL (Google Sheets, Drive, OneDrive)
            rid: Request ID for logging
        
        Returns:
            ProcessedFile with extracted data
        """
        # Determine source
        if url:
            source = self.detect_source(url)
            
            if source == FileSource.GOOGLE_SHEETS:
                return self.process_google_sheets(url, rid)
            elif source == FileSource.GOOGLE_DRIVE:
                return self.process_google_drive(url, rid)
            elif source == FileSource.ONEDRIVE:
                return self.process_onedrive(url, rid)
        
        # Process local file
        if file_bytes and file_name:
            return self.process_local_file(file_bytes, file_name, rid)
        
        # Invalid input
        return ProcessedFile(
            success=False,
            file_type=FileType.UNKNOWN,
            source=FileSource.LOCAL,
            error="Must provide either (file_bytes + file_name) or url"
        )


# Global service instance
enhanced_file_processor = EnhancedFileProcessor()


def process_file(file_bytes: bytes = None, file_name: str = None, url: str = None, **kwargs) -> ProcessedFile:
    """Convenience function for file processing"""
    return enhanced_file_processor.process_file(file_bytes, file_name, url, **kwargs)
