from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

def get_current_workspace(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    if settings.AUTH_DISABLED:
        return "ws_local_dev"
        
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")
        
    # TODO: In production, verify the JWT using settings.JWT_JWKS_URL
    # For now, if AUTH_DISABLED is False, we require the token to be the workspace_id for testing
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    return token
