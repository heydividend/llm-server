import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verify the API key from the Authorization header.
    
    Expected format: Authorization: Bearer YOUR_API_KEY
    
    Raises:
        HTTPException: 401 if the API key is missing, invalid format, or doesn't match
    """
    api_key = os.getenv("HARVEY_AI_API_KEY")
    
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: HARVEY_AI_API_KEY not set"
        )
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use: Bearer YOUR_KEY"
        )
    
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return credentials.credentials
