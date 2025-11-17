"""
OneDrive Integration Service

Allows Harvey to access and download files from Microsoft OneDrive.
Supports:
- OAuth authenticated file access
- Portfolio files (PDF, CSV, Excel, images)
- Personal and business OneDrive accounts
"""

import os
import re
import logging
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("onedrive")


@dataclass
class OneDriveFileData:
    """File data from OneDrive"""
    success: bool
    file_name: str = ""
    file_bytes: bytes = None
    mime_type: str = ""
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.file_bytes is None:
            self.file_bytes = b""


class OneDriveService:
    """
    OneDrive integration for downloading portfolio files.
    
    Features:
    - OAuth 2.0 authentication with Microsoft Graph API
    - Download files from personal/business OneDrive
    - Support PDF, CSV, Excel, images
    """
    
    def __init__(self):
        self.enabled = False
        self.access_token = None
        
        # Microsoft Graph API configuration
        self.client_id = os.getenv("ONEDRIVE_CLIENT_ID")
        self.client_secret = os.getenv("ONEDRIVE_CLIENT_SECRET")
        self.tenant_id = os.getenv("ONEDRIVE_TENANT_ID", "common")
        
        if self.client_id and self.client_secret:
            try:
                import msal
                self.msal = msal
                self.enabled = True
                logger.info("✅ OneDrive service initialized")
            except ImportError:
                logger.error(
                    "msal package not installed. "
                    "Run: pip install msal"
                )
        else:
            logger.warning(
                "OneDrive disabled: No credentials found. "
                "Set ONEDRIVE_CLIENT_ID and ONEDRIVE_CLIENT_SECRET"
            )
    
    def get_access_token(self) -> Optional[str]:
        """
        Get access token using client credentials flow (app-only access).
        For user-delegated access, implement device code flow or web auth.
        """
        if not self.enabled:
            return None
        
        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = self.msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret
            )
            
            # Acquire token for Microsoft Graph
            result = app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                logger.info("✅ OneDrive access token acquired")
                return self.access_token
            else:
                error = result.get("error_description", "Unknown error")
                logger.error(f"Failed to acquire token: {error}")
                return None
        
        except Exception as e:
            logger.error(f"OneDrive authentication failed: {e}")
            return None
    
    def extract_file_info(self, url_or_path: str) -> Optional[Dict[str, str]]:
        """
        Extract file information from OneDrive URL or path.
        
        Supported formats:
        - https://onedrive.live.com/... (sharing link)
        - /drive/items/{item-id} (Graph API path)
        - item-id (direct item ID)
        """
        url_or_path = url_or_path.strip()
        
        # Check for sharing link
        if "onedrive.live.com" in url_or_path or "1drv.ms" in url_or_path:
            # For sharing links, we need to resolve them using Graph API
            return {"type": "sharing_link", "url": url_or_path}
        
        # Check for item ID in path
        item_id_match = re.search(r'/items/([a-zA-Z0-9_-]+)', url_or_path)
        if item_id_match:
            return {"type": "item_id", "id": item_id_match.group(1)}
        
        # Direct item ID
        if re.match(r'^[a-zA-Z0-9_-]+$', url_or_path):
            return {"type": "item_id", "id": url_or_path}
        
        return None
    
    def download_file(
        self,
        file_url_or_id: str,
        rid: Optional[str] = None
    ) -> OneDriveFileData:
        """
        Download a file from OneDrive.
        
        Args:
            file_url_or_id: OneDrive URL or item ID
            rid: Request ID for logging
        
        Returns:
            OneDriveFileData with file content
        """
        if not self.enabled:
            return OneDriveFileData(
                success=False,
                error="OneDrive service not enabled. Configure ONEDRIVE_CLIENT_ID and ONEDRIVE_CLIENT_SECRET."
            )
        
        log_prefix = f"[{rid}]" if rid else ""
        
        # Get access token
        if not self.access_token:
            if not self.get_access_token():
                return OneDriveFileData(
                    success=False,
                    error="Failed to authenticate with OneDrive"
                )
        
        # Extract file info
        file_info = self.extract_file_info(file_url_or_id)
        if not file_info:
            return OneDriveFileData(
                success=False,
                error=f"Invalid OneDrive URL or file ID: {file_url_or_id}"
            )
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Build Graph API URL
            if file_info["type"] == "item_id":
                item_id = file_info["id"]
                metadata_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}"
                download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content"
            else:
                return OneDriveFileData(
                    success=False,
                    error="Sharing links not yet supported. Use item ID or path."
                )
            
            # Get file metadata
            logger.info(f"{log_prefix} Fetching OneDrive file metadata: {item_id}")
            metadata_response = requests.get(metadata_url, headers=headers)
            metadata_response.raise_for_status()
            metadata = metadata_response.json()
            
            file_name = metadata.get('name', 'unknown')
            mime_type = metadata.get('file', {}).get('mimeType', '')
            
            # Download file content
            logger.info(f"{log_prefix} Downloading OneDrive file: {file_name}")
            download_response = requests.get(download_url, headers=headers)
            download_response.raise_for_status()
            
            file_bytes = download_response.content
            
            logger.info(
                f"{log_prefix} OneDrive download successful: "
                f"{file_name} ({len(file_bytes)} bytes)"
            )
            
            return OneDriveFileData(
                success=True,
                file_name=file_name,
                file_bytes=file_bytes,
                mime_type=mime_type
            )
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, try to refresh
                self.access_token = None
                logger.warning(f"{log_prefix} Access token expired, retrying...")
                return self.download_file(file_url_or_id, rid)
            
            error_msg = f"OneDrive API error: {e.response.status_code} - {e.response.text}"
            logger.error(f"{log_prefix} {error_msg}")
            return OneDriveFileData(
                success=False,
                error=error_msg
            )
        
        except Exception as e:
            error_msg = f"Failed to download OneDrive file: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            return OneDriveFileData(
                success=False,
                error=error_msg
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health and configuration"""
        return {
            "enabled": self.enabled,
            "has_credentials": bool(self.client_id and self.client_secret),
            "has_token": self.access_token is not None,
            "status": "healthy" if self.enabled else "disabled"
        }


# Global service instance
onedrive_service = OneDriveService()


def download_from_onedrive(url_or_id: str, **kwargs) -> OneDriveFileData:
    """Convenience function to download an OneDrive file"""
    return onedrive_service.download_file(url_or_id, **kwargs)
