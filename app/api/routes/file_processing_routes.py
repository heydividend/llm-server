"""
Enhanced File Processing API Routes

Unified endpoint for processing portfolio files from multiple sources:
- Local uploads: PDF, CSV, XLS, XLSX, JPG, PNG, JPEG
- Google Sheets: Direct spreadsheet URLs
- Google Drive: File download and processing
- OneDrive: File download and processing
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel, Field
import os

from app.core.auth import verify_api_key
from app.services.enhanced_file_processor import enhanced_file_processor
from app.services.portfolio_parser import portfolio_parser
from app.core.logging_config import get_logger

logger = get_logger("file_processing_routes")

router = APIRouter()

MAX_FILE_SIZE_BYTES = 52428800
ALLOWED_EXTENSIONS = {'.pdf', '.csv', '.xlsx', '.xls', '.jpg', '.jpeg', '.png'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'text/csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'image/jpeg',
    'image/png',
    'application/octet-stream'
}


def validate_file_upload(file: UploadFile, file_bytes: bytes) -> None:
    """
    Validate uploaded file for security.
    
    Raises:
        HTTPException: If validation fails
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // 1048576}MB"
        )
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Unexpected MIME type: {file.content_type} for file {file.filename}")


def sanitize_error_message(error: str) -> str:
    """
    Sanitize error messages to avoid leaking internal implementation details.
    
    Args:
        error: Original error message
        
    Returns:
        Sanitized error message safe for API response
    """
    sensitive_keywords = [
        'traceback', 'exception', 'azure', 'api key', 'secret', 'password',
        'connection string', 'database', 'internal', 'stack trace', 'token'
    ]
    
    error_lower = error.lower()
    for keyword in sensitive_keywords:
        if keyword in error_lower:
            return "An error occurred while processing your file. Please try again or contact support."
    
    if len(error) > 200:
        return "File processing failed. Please check your file format and try again."
    
    return error


class CloudFileRequest(BaseModel):
    """Request for processing cloud-stored files"""
    url: str = Field(..., description="Google Sheets, Google Drive, or OneDrive URL")
    include_summary: bool = Field(default=True, description="Include portfolio summary")


class FileProcessingResponse(BaseModel):
    """Response from file processing"""
    success: bool
    file_type: str
    source: str
    holdings_count: int = 0
    portfolio_summary: Optional[str] = None
    extracted_text: Optional[str] = None
    tickers: list = []
    tables: list = []
    metadata: dict = {}
    error: Optional[str] = None


@router.post("/files/upload", response_model=FileProcessingResponse)
async def upload_and_process_file(
    file: UploadFile = File(...),
    include_summary: bool = Form(default=True),
    api_key: str = Depends(verify_api_key)
):
    """
    Upload and process a portfolio file.
    
    **Supported file types:**
    - PDF documents
    - CSV files
    - Excel files (XLS, XLSX)
    - Images (JPG, PNG, JPEG)
    
    **Maximum file size:** 50MB
    
    **Returns:**
    - Extracted portfolio holdings
    - Portfolio summary with analysis
    - Ticker symbols
    - Raw extracted text
    """
    try:
        filename = file.filename or "unknown_file"
        logger.info(f"Processing uploaded file: {filename}")
        
        file_bytes = await file.read()
        
        validate_file_upload(file, file_bytes)
        
        result = enhanced_file_processor.process_file(
            file_bytes=file_bytes,
            file_name=filename,
            rid="upload"
        )
        
        if not result.success:
            error_msg = sanitize_error_message(result.error or "Unknown error")
            logger.error(f"File processing failed: {result.error}")
            raise HTTPException(status_code=422, detail=error_msg)
        
        tickers = portfolio_parser.extract_tickers_list(result.portfolio_holdings)
        
        portfolio_summary = None
        if include_summary and result.portfolio_holdings:
            portfolio_summary = portfolio_parser.format_holdings_summary(result.portfolio_holdings)
        
        logger.info(
            f"File processing successful: {len(result.portfolio_holdings)} holdings, "
            f"{len(tickers)} tickers"
        )
        
        return FileProcessingResponse(
            success=True,
            file_type=result.file_type.value,
            source=result.source.value,
            holdings_count=len(result.portfolio_holdings),
            portfolio_summary=portfolio_summary,
            extracted_text=result.extracted_text if len(result.extracted_text) < 10000 else result.extracted_text[:10000] + "...",
            tickers=tickers,
            tables=result.tables[:5] if result.tables else [],
            metadata=result.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing error: {e}", exc_info=True)
        error_msg = sanitize_error_message(str(e))
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/files/cloud", response_model=FileProcessingResponse)
async def process_cloud_file(
    request: CloudFileRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Process a file from cloud storage.
    
    **Supported sources:**
    - Google Sheets: `https://docs.google.com/spreadsheets/d/...`
    - Google Drive: `https://drive.google.com/file/d/...`
    - OneDrive: `https://onedrive.live.com/...`
    
    **Maximum file size:** 50MB
    
    **Returns:**
    - Extracted portfolio holdings
    - Portfolio summary with analysis
    - Ticker symbols
    """
    try:
        logger.info(f"Processing cloud file from URL")
        
        if not request.url or len(request.url) < 10:
            raise HTTPException(status_code=400, detail="Invalid URL provided")
        
        result = enhanced_file_processor.process_file(
            url=request.url,
            rid="cloud"
        )
        
        if not result.success:
            error_msg = sanitize_error_message(result.error or "Unknown error")
            logger.error(f"Cloud file processing failed: {result.error}")
            raise HTTPException(status_code=422, detail=error_msg)
        
        tickers = portfolio_parser.extract_tickers_list(result.portfolio_holdings)
        
        portfolio_summary = None
        if request.include_summary and result.portfolio_holdings:
            portfolio_summary = portfolio_parser.format_holdings_summary(result.portfolio_holdings)
        
        logger.info(
            f"Cloud file processing successful: {len(result.portfolio_holdings)} holdings, "
            f"{len(tickers)} tickers"
        )
        
        return FileProcessingResponse(
            success=True,
            file_type=result.file_type.value,
            source=result.source.value,
            holdings_count=len(result.portfolio_holdings),
            portfolio_summary=portfolio_summary,
            extracted_text=result.extracted_text if len(result.extracted_text) < 10000 else result.extracted_text[:10000] + "...",
            tickers=tickers,
            tables=result.tables[:5] if result.tables else [],
            metadata=result.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cloud file processing error: {e}", exc_info=True)
        error_msg = sanitize_error_message(str(e))
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/files/health")
async def file_processing_health(api_key: str = Depends(verify_api_key)):
    """
    Check health status of all file processing services.
    """
    try:
        health_status: dict = {
            "azure_document_intelligence": "unknown",
            "google_sheets": "unknown",
            "google_drive": "unknown",
            "onedrive": "unknown",
            "overall_status": "healthy"
        }
        
        try:
            result = enhanced_file_processor.azure_di.health_check()
            health_status["azure_document_intelligence"] = result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.warning(f"Azure DI health check failed: {e}")
            health_status["azure_document_intelligence"] = "unavailable"
        
        try:
            result = enhanced_file_processor.google_sheets.health_check()
            health_status["google_sheets"] = result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.warning(f"Google Sheets health check failed: {e}")
            health_status["google_sheets"] = "unavailable"
        
        try:
            result = enhanced_file_processor.google_drive.health_check()
            health_status["google_drive"] = result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.warning(f"Google Drive health check failed: {e}")
            health_status["google_drive"] = "unavailable"
        
        try:
            result = enhanced_file_processor.onedrive.health_check()
            health_status["onedrive"] = result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.warning(f"OneDrive health check failed: {e}")
            health_status["onedrive"] = "unavailable"
        
        return JSONResponse(health_status)
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail="Service health check unavailable")


@router.get("/files/supported-types")
async def get_supported_file_types():
    """
    Get list of supported file types and cloud sources.
    """
    return JSONResponse({
        "local_file_types": [
            "pdf",
            "csv",
            "xlsx",
            "xls",
            "jpg",
            "jpeg",
            "png"
        ],
        "cloud_sources": [
            {
                "name": "Google Sheets",
                "url_pattern": "https://docs.google.com/spreadsheets/d/...",
                "example": "https://docs.google.com/spreadsheets/d/1ABC...xyz/edit",
                "auth_required": True
            },
            {
                "name": "Google Drive",
                "url_pattern": "https://drive.google.com/file/d/...",
                "example": "https://drive.google.com/file/d/1ABC...xyz/view",
                "auth_required": True
            },
            {
                "name": "OneDrive",
                "url_pattern": "https://onedrive.live.com/...",
                "example": "https://onedrive.live.com/...",
                "auth_required": True
            }
        ],
        "max_file_size_mb": 50,
        "note": "Cloud sources require OAuth credentials. Set environment variables for service accounts."
    })
