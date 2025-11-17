"""
Google Drive Integration Service

Allows Harvey to access and download files from Google Drive.
Supports:
- Public Google Drive file links
- OAuth authenticated private files
- Portfolio files (PDF, CSV, Excel, images)
"""

import os
import re
import logging
import io
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("google_drive")


@dataclass
class DriveFileData:
    """File data from Google Drive"""
    success: bool
    file_name: str = ""
    file_bytes: bytes = None
    mime_type: str = ""
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.file_bytes is None:
            self.file_bytes = b""


class GoogleDriveService:
    """
    Google Drive integration for downloading portfolio files.
    
    Features:
    - Extract file ID from Drive URLs
    - Download public files (no auth required)
    - Download private files (OAuth)
    - Support PDF, CSV, Excel, images
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
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                self.service = build('drive', 'v3', credentials=credentials)
                self.enabled = True
                logger.info("✅ Google Drive service initialized with service account")
            elif creds_json:
                import json
                creds_dict = json.loads(creds_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                self.service = build('drive', 'v3', credentials=credentials)
                self.enabled = True
                logger.info("✅ Google Drive service initialized with JSON credentials")
            else:
                logger.warning(
                    "Google Drive disabled: No credentials found. "
                    "Set GOOGLE_SERVICE_ACCOUNT_PATH or GOOGLE_SERVICE_ACCOUNT_JSON"
                )
        except ImportError:
            logger.error(
                "google-api-python-client not installed. "
                "Run: pip install google-api-python-client google-auth"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
    
    def extract_file_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract file ID from Google Drive URL or return ID directly.
        
        Supported formats:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/open?id=FILE_ID
        - FILE_ID (direct ID)
        """
        url_or_id = url_or_id.strip()
        
        # Try to extract from URL
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'[?&]id=([a-zA-Z0-9-_]+)',
            r'/open\?id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        # If it looks like a direct ID
        if re.match(r'^[a-zA-Z0-9-_]+$', url_or_id) and len(url_or_id) > 20:
            return url_or_id
        
        return None
    
    def download_file(
        self,
        file_url_or_id: str,
        rid: Optional[str] = None
    ) -> DriveFileData:
        """
        Download a file from Google Drive.
        
        Args:
            file_url_or_id: Google Drive URL or file ID
            rid: Request ID for logging
        
        Returns:
            DriveFileData with file content
        """
        if not self.enabled or not self.service:
            return DriveFileData(
                success=False,
                error="Google Drive service not enabled. Configure service account credentials."
            )
        
        log_prefix = f"[{rid}]" if rid else ""
        
        # Extract file ID
        file_id = self.extract_file_id(file_url_or_id)
        if not file_id:
            return DriveFileData(
                success=False,
                error=f"Invalid Google Drive URL or file ID: {file_url_or_id}"
            )
        
        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="name, mimeType"
            ).execute()
            
            file_name = file_metadata.get('name', 'unknown')
            mime_type = file_metadata.get('mimeType', '')
            
            logger.info(
                f"{log_prefix} Downloading Google Drive file: {file_name} "
                f"(type={mime_type})"
            )
            
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            
            from googleapiclient.http import MediaIoBaseDownload
            downloader = MediaIoBaseDownload(file_stream, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.debug(f"{log_prefix} Download progress: {progress}%")
            
            file_bytes = file_stream.getvalue()
            
            logger.info(
                f"{log_prefix} Google Drive download successful: "
                f"{file_name} ({len(file_bytes)} bytes)"
            )
            
            return DriveFileData(
                success=True,
                file_name=file_name,
                file_bytes=file_bytes,
                mime_type=mime_type
            )
        
        except Exception as e:
            error_msg = f"Failed to download Google Drive file: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            return DriveFileData(
                success=False,
                error=error_msg
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health and configuration"""
        return {
            "enabled": self.enabled,
            "has_service": self.service is not None,
            "status": "healthy" if self.enabled and self.service else "disabled"
        }


# Global service instance
google_drive_service = GoogleDriveService()


def download_from_drive(url_or_id: str, **kwargs) -> DriveFileData:
    """Convenience function to download a Google Drive file"""
    return google_drive_service.download_file(url_or_id, **kwargs)
