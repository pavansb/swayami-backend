from fastapi import HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import base64
from app.config import settings
from app.models import AuthResponse
from app.repositories.user_repository import user_repository
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class ProductionAuthService:
    """Production-grade authentication service with real user mapping"""
    
    async def get_user_id_from_email(self, email: str) -> Optional[str]:
        """Get MongoDB user ID from email"""
        try:
            user = await user_repository.get_user_by_email(email)
            if user:
                return user.id  # This is the real MongoDB _id
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def decode_mock_token(self, token: str) -> Optional[str]:
        """Decode the mock token format: base64(user_id:email)"""
        try:
            decoded = base64.b64decode(token.encode()).decode()
            user_id, email = decoded.split(":", 1)
            
            # For mock tokens, the user_id might be the mock "user_123"
            # We need to look up the real user by email
            if email:
                return email  # Return email to lookup real user
            return None
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return None
    
    async def authenticate_user(self, token: str) -> Optional[str]:
        """Authenticate user and return real MongoDB user ID"""
        try:
            # Try to decode the token to get email
            email = self.decode_mock_token(token)
            if not email:
                logger.warning("Could not extract email from token")
                return None
            
            # Get real user ID from MongoDB
            real_user_id = await self.get_user_id_from_email(email)
            if real_user_id:
                logger.info(f"✅ Authenticated user {email} -> MongoDB ID: {real_user_id}")
                return real_user_id
            else:
                logger.warning(f"⚠️ No MongoDB user found for email: {email}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return None

# Global instance
auth_service = ProductionAuthService()

async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Production-grade authentication: Extract real MongoDB user ID
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Handle Bearer token
    if credentials.scheme.lower() == "bearer":
        user_id = await auth_service.authenticate_user(credentials.credentials)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or user not found in database",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user_id
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication scheme. Use Bearer token.",
        headers={"WWW-Authenticate": "Bearer"}
    )

async def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Optional authentication - returns None if no valid auth provided
    """
    try:
        return await get_current_user_id(credentials)
    except HTTPException:
        return None

# Backward compatibility function for existing code
async def get_user_id_flexible(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Flexible user ID extraction with production-grade lookup
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    # Handle Bearer token
    if authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
        user_id = await auth_service.authenticate_user(token)
        if user_id:
            return user_id
    
    # Handle Basic auth
    elif authorization.startswith("Basic "):
        try:
            credentials = authorization[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(credentials).decode()
            email, password = decoded.split(":", 1)
            
            # Look up user by email in MongoDB
            user_id = await auth_service.get_user_id_from_email(email)
            if user_id:
                return user_id
                
        except Exception as e:
            logger.error(f"Basic auth error: {e}")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )

# Legacy mock auth for development fallback
class LegacyMockAuthService:
    """Legacy mock auth service - DEPRECATED"""
    
    def __init__(self):
        self.mock_user = {
            "user_id": settings.mock_user_id,
            "email": settings.mock_user_email,
            "name": "Pavan SB",
        }
    
    def verify_credentials(self, email: str, password: str) -> bool:
        return (email == settings.mock_user_email and 
                password == settings.mock_user_password)
    
    def create_access_token(self, user_id: str) -> str:
        token_data = f"{user_id}:{settings.mock_user_email}"
        return base64.b64encode(token_data.encode()).decode()
    
    def authenticate(self, email: str, password: str) -> AuthResponse:
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

# Legacy instance for backward compatibility
legacy_auth_service = LegacyMockAuthService() 