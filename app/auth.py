from fastapi import HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import base64
from app.config import settings
from app.models import AuthResponse
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class MockAuthService:
    """Mock authentication service for development"""
    
    def __init__(self):
        self.mock_user = {
            "user_id": settings.mock_user_id,
            "email": settings.mock_user_email,
            "name": "Pavan SB",
        }
    
    def verify_credentials(self, email: str, password: str) -> bool:
        """Verify mock credentials"""
        return (email == settings.mock_user_email and 
                password == settings.mock_user_password)
    
    def create_access_token(self, user_id: str) -> str:
        """Create a mock access token"""
        # In production, this would create a proper JWT token
        token_data = f"{user_id}:{settings.mock_user_email}"
        return base64.b64encode(token_data.encode()).decode()
    
    def decode_token(self, token: str) -> Optional[str]:
        """Decode mock access token"""
        try:
            decoded = base64.b64decode(token.encode()).decode()
            user_id, email = decoded.split(":", 1)
            if email == settings.mock_user_email:
                return user_id
        except Exception:
            pass
        return None
    
    def authenticate(self, email: str, password: str) -> AuthResponse:
        """Authenticate user and return auth response"""
        if not self.verify_credentials(email, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        access_token = self.create_access_token(self.mock_user["user_id"])
        
        return AuthResponse(
            user_id=self.mock_user["user_id"],
            email=self.mock_user["email"],
            name=self.mock_user["name"],
            access_token=access_token
        )

# Global instance
auth_service = MockAuthService()

async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Extract user_id from authorization header
    Supports both Bearer token and Basic auth for development
    """
    if not settings.mock_auth_enabled:
        # In production, this would validate real JWT tokens
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Real authentication not implemented yet"
        )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Handle Bearer token
    if credentials.scheme.lower() == "bearer":
        user_id = auth_service.decode_token(credentials.credentials)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user_id
    
    # Handle Basic auth (for testing)
    elif credentials.scheme.lower() == "basic":
        try:
            decoded = base64.b64decode(credentials.credentials).decode()
            email, password = decoded.split(":", 1)
            if auth_service.verify_credentials(email, password):
                return settings.mock_user_id
        except Exception:
            pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

async def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Optional authentication - returns None if no valid auth provided
    Useful for endpoints that work with or without authentication
    """
    try:
        return await get_current_user_id(credentials)
    except HTTPException:
        return None

# Alternative dependency for development - allows both auth methods
async def get_user_id_flexible(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Flexible user ID extraction for development
    Supports multiple auth methods for easier testing
    """
    if not settings.mock_auth_enabled:
        return settings.mock_user_id  # Fallback for development
    
    if not authorization:
        # For development, allow requests without auth
        logger.warning("No authorization header provided, using mock user")
        return settings.mock_user_id
    
    # Handle Bearer token
    if authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
        user_id = auth_service.decode_token(token)
        if user_id:
            return user_id
    
    # Handle Basic auth
    elif authorization.startswith("Basic "):
        try:
            credentials = authorization[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(credentials).decode()
            email, password = decoded.split(":", 1)
            if auth_service.verify_credentials(email, password):
                return settings.mock_user_id
        except Exception:
            pass
    
    # Handle simple email:password format for testing
    elif ":" in authorization:
        try:
            email, password = authorization.split(":", 1)
            if auth_service.verify_credentials(email, password):
                return settings.mock_user_id
        except Exception:
            pass
    
    # Fallback to mock user for development
    logger.warning(f"Invalid authorization format, using mock user: {authorization[:20]}...")
    return settings.mock_user_id 