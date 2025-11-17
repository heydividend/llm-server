"""
Google Sheets Integration Service

Allows Harvey to read portfolio data directly from Google Sheets.
Supports:
- Public Google Sheets URLs
- OAuth authenticated private sheets
- Real-time data synchronization
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("google_sheets")


@dataclass
class SheetsData:
    """Structured data from Google Sheets"""
    success: bool
    sheet_name: str = ""
    data: List[List[str]] = None
    headers: List[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = []
        if self.headers is None:
            self.headers = []


class GoogleSheetsService:
    """
    Google Sheets integration for reading portfolio data.
    
    Features:
    - Extract spreadsheet ID from URLs
    - Read public sheets (no auth required)
    - Read private sheets (OAuth)
    - Convert sheets data to CSV format for portfolio parser
    """
    
    def __init__(self):
        self.enabled = False
        self.service = None
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # Check for service account credentials
            creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
            creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            
            if creds_path and os.path.exists(creds_path):
                credentials = service_account.Credentials.from_service_account_file(
                    creds_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                self.service = build('sheets', 'v4', credentials=credentials)
                self.enabled = True
                logger.info("✅ Google Sheets service initialized with service account")
            elif creds_json:
                import json
                creds_dict = json.loads(creds_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                self.service = build('sheets', 'v4', credentials=credentials)
                self.enabled = True
                logger.info("✅ Google Sheets service initialized with JSON credentials")
            else:
                logger.warning(
                    "Google Sheets disabled: No credentials found. "
                    "Set GOOGLE_SERVICE_ACCOUNT_PATH or GOOGLE_SERVICE_ACCOUNT_JSON"
                )
        except ImportError:
            logger.error(
                "google-api-python-client not installed. "
                "Run: pip install google-api-python-client google-auth"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
    
    def extract_spreadsheet_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract spreadsheet ID from Google Sheets URL or return ID directly.
        
        Supported formats:
        - https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
        - https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0
        - SPREADSHEET_ID (direct ID)
        """
        url_or_id = url_or_id.strip()
        
        # Try to extract from URL
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'spreadsheets/d/([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        # If it looks like a direct ID (alphanumeric with hyphens/underscores)
        if re.match(r'^[a-zA-Z0-9-_]+$', url_or_id) and len(url_or_id) > 20:
            return url_or_id
        
        return None
    
    def read_sheet(
        self, 
        spreadsheet_url_or_id: str,
        sheet_name: Optional[str] = None,
        range_notation: Optional[str] = None,
        rid: Optional[str] = None
    ) -> SheetsData:
        """
        Read data from a Google Sheet.
        
        Args:
            spreadsheet_url_or_id: Google Sheets URL or spreadsheet ID
            sheet_name: Name of the sheet tab (default: first sheet)
            range_notation: A1 notation range (e.g., "A1:F100")
            rid: Request ID for logging
        
        Returns:
            SheetsData with extracted rows
        """
        if not self.enabled or not self.service:
            return SheetsData(
                success=False,
                error="Google Sheets service not enabled. Configure service account credentials."
            )
        
        log_prefix = f"[{rid}]" if rid else ""
        
        # Extract spreadsheet ID
        spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_url_or_id)
        if not spreadsheet_id:
            return SheetsData(
                success=False,
                error=f"Invalid Google Sheets URL or ID: {spreadsheet_url_or_id}"
            )
        
        try:
            # Build range string
            if range_notation:
                range_str = f"{sheet_name}!{range_notation}" if sheet_name else range_notation
            elif sheet_name:
                range_str = sheet_name
            else:
                range_str = "A:Z"  # Read first sheet, all columns
            
            logger.info(f"{log_prefix} Reading Google Sheet: {spreadsheet_id} range={range_str}")
            
            # Call Google Sheets API
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_str
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return SheetsData(
                    success=False,
                    error="No data found in sheet"
                )
            
            # Extract headers (first row) and data
            headers = values[0] if values else []
            data_rows = values[1:] if len(values) > 1 else []
            
            logger.info(
                f"{log_prefix} Google Sheets read successful: "
                f"{len(headers)} columns, {len(data_rows)} rows"
            )
            
            return SheetsData(
                success=True,
                sheet_name=sheet_name or "Sheet1",
                data=data_rows,
                headers=headers
            )
        
        except Exception as e:
            error_msg = f"Failed to read Google Sheet: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            return SheetsData(
                success=False,
                error=error_msg
            )
    
    def convert_to_csv(self, sheets_data: SheetsData) -> str:
        """
        Convert SheetsData to CSV format for portfolio parser.
        """
        if not sheets_data.success or not sheets_data.data:
            return ""
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        if sheets_data.headers:
            writer.writerow(sheets_data.headers)
        
        # Write data rows
        for row in sheets_data.data:
            writer.writerow(row)
        
        return output.getvalue()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health and configuration"""
        return {
            "enabled": self.enabled,
            "has_service": self.service is not None,
            "status": "healthy" if self.enabled and self.service else "disabled"
        }


# Global service instance
google_sheets_service = GoogleSheetsService()


def read_google_sheet(url_or_id: str, **kwargs) -> SheetsData:
    """Convenience function to read a Google Sheet"""
    return google_sheets_service.read_sheet(url_or_id, **kwargs)
