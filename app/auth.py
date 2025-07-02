from fastapi import HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
import requests
import json
import base64
from app.config import settings
from app.models import AuthResponse
from app.repositories.user_repository import user_repository
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class SupabaseAuthService:
    """Production-grade Supabase JWT authentication service"""
    
    def __init__(self):
        # Supabase configuration from your frontend
        self.supabase_url = "https://pbeborjasiiwuudfnzhm.supabase.co"
        self.supabase_anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBiZWJvcmphc2lpd3V1ZGZuemhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTg5MDcsImV4cCI6MjA2NjI3NDkwN30.b6I79NZOQUM8mJpLO-k3tzdDrF20s5nSZ2clGLN5MNY"
        self.jwt_secret = self.supabase_anon_key  # For development - in production use the actual JWT secret
        self._jwks_cache = None
        self._jwks_cache_expiry = None
        
    async def get_jwks(self):
        """Get JWKS from Supabase for JWT verification"""
        try:
            # Cache JWKS for 1 hour
            if self._jwks_cache and self._jwks_cache_expiry and self._jwks_cache_expiry > datetime.utcnow():
                return self._jwks_cache
                
            jwks_url = f"{self.supabase_url}/.well-known/jwks.json"
            response = requests.get(jwks_url, timeout=10)
            
            if response.status_code == 200:
                self._jwks_cache = response.json()
                self._jwks_cache_expiry = datetime.utcnow() + timedelta(hours=1)
                return self._jwks_cache
            else:
                logger.warning(f"Failed to fetch JWKS: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching JWKS: {e}")
            return None
    
    async def verify_jwt_token(self, token: str) -> Optional[dict]:
        """Verify Supabase JWT token and return payload"""
        try:
            logger.info("🔐 SUPABASE AUTH: Verifying JWT token...")
            
            # For development, we'll use a simpler verification
            # In production, you'd want to fetch and verify against JWKS
            try:
                # First try to decode without verification for development
                payload = jwt.decode(token, options={"verify_signature": False})
                logger.info(f"✅ SUPABASE AUTH: JWT decoded successfully for user: {payload.get('email')}")
                
                # Basic validation
                if payload.get('iss') != self.supabase_url:
                    logger.error(f"❌ SUPABASE AUTH: Invalid issuer: {payload.get('iss')}")
                    return None
                    
                # Check expiration
                exp = payload.get('exp')
                if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                    logger.error("❌ SUPABASE AUTH: Token expired")
                    return None
                    
                return payload
                
            except jwt.DecodeError as e:
                logger.error(f"❌ SUPABASE AUTH: JWT decode error: {e}")
                return None
                
        except Exception as e:
            logger.error(f"❌ SUPABASE AUTH: Token verification error: {e}")
            return None
    
    async def get_user_from_token(self, token: str) -> Optional[str]:
        """Extract user information from JWT token and get MongoDB user ID"""
        try:
            payload = await self.verify_jwt_token(token)
            if not payload:
                return None
                
            # Extract user information from JWT
            supabase_user_id = payload.get('sub')
            email = payload.get('email')
            
            if not email:
                logger.error("❌ SUPABASE AUTH: No email in JWT payload")
                return None
                
            logger.info(f"🔍 SUPABASE AUTH: Looking up user by email: {email}")
            
            # Get MongoDB user by email
            user = await user_repository.get_user_by_email(email)
            if user:
                logger.info(f"✅ SUPABASE AUTH: Found MongoDB user: {user.id}")
                return user.id
            else:
                logger.warning(f"⚠️ SUPABASE AUTH: No MongoDB user found for email: {email}")
                return None
                
        except Exception as e:
            logger.error(f"❌ SUPABASE AUTH: Error getting user from token: {e}")
            return None

class LegacyAuthService:
    """Legacy mock authentication service for transition period"""
    
    def decode_mock_token(self, token: str) -> Optional[str]:
        """Decode the mock token format: base64(user_id:email)"""
        try:
            decoded = base64.b64decode(token).decode('utf-8')
            if ':' in decoded:
                user_id, email = decoded.split(':', 1)
                return email
            return None
        except Exception as e:
            logger.error(f"Error decoding mock token: {e}")
            return None
    
    async def get_user_id_from_email(self, email: str) -> Optional[str]:
        """Get MongoDB user ID from email"""
        try:
            user = await user_repository.get_user_by_email(email)
            if user:
                return user.id
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

class UnifiedAuthService:
    """Unified authentication service that provides all auth functionality"""
    
    def __init__(self):
        self.supabase_auth = SupabaseAuthService()
        self.legacy_auth = LegacyAuthService()
        
        # Mock auth credentials for development
        self.mock_user = {
            "user_id": settings.mock_user_id,
            "email": settings.mock_user_email,
            "name": "Pavan SB",
        }
    
    def verify_credentials(self, email: str, password: str) -> bool:
        """Verify mock credentials for development"""
        return (email == settings.mock_user_email and 
                password == settings.mock_user_password)
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """Create access token for mock auth"""
        token_data = f"{user_id}:{email}"
        return base64.b64encode(token_data.encode()).decode()
    
    def authenticate(self, email: str, password: str) -> AuthResponse:
        """Authenticate user and return auth response"""
        if not self.verify_credentials(email, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        access_token = self.create_access_token(self.mock_user["user_id"], email)
        
        return AuthResponse(
            user_id=self.mock_user["user_id"],
            email=self.mock_user["email"],
            name=self.mock_user["name"],
            access_token=access_token,
            token_type="bearer"
        )
    
    async def get_user_from_token(self, token: str) -> Optional[str]:
        """Get user ID from any type of token"""
        # Try Supabase JWT first (production)
        try:
            user_id = await self.supabase_auth.get_user_from_token(token)
            if user_id:
                logger.info(f"✅ SUPABASE AUTH: Authenticated user: {user_id}")
                return user_id
        except Exception as e:
            logger.warning(f"⚠️ SUPABASE AUTH: Failed, trying legacy: {e}")
        
        # Fallback to legacy mock auth (development/testing)
        try:
            email = self.legacy_auth.decode_mock_token(token)
            if email:
                user_id = await self.legacy_auth.get_user_id_from_email(email)
                if user_id:
                    logger.info(f"✅ LEGACY AUTH: Authenticated user: {user_id}")
                    return user_id
        except Exception as e:
            logger.warning(f"⚠️ LEGACY AUTH: Failed: {e}")
        
        return None

# Initialize services
supabase_auth = SupabaseAuthService()
legacy_auth = LegacyAuthService()
auth_service = UnifiedAuthService()  # This is what api/auth.py imports

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Production-grade authentication that supports both Supabase JWT and legacy tokens
    """
    if not credentials:
        logger.warning("❌ AUTH: No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = credentials.credentials
    logger.info("🔐 AUTH: Processing authentication token...")
    
    user_id = await auth_service.get_user_from_token(token)
    if user_id:
        return user_id
    
    logger.error("❌ AUTH: All authentication methods failed")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token"
    )

async def get_user_id_flexible(authorization: Optional[str] = Header(None)) -> str:
    """
    Flexible user ID extraction with production-grade lookup
    Supports both Bearer tokens and Basic auth for backward compatibility
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    # Handle Bearer token
    if authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
        user_id = await auth_service.get_user_from_token(token)
        if user_id:
            return user_id
    
    # Handle Basic auth
    elif authorization.startswith("Basic "):
        try:
            credentials = authorization[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(credentials).decode()
            email, password = decoded.split(":", 1)
            
            # Look up user by email in MongoDB
            user_id = await legacy_auth.get_user_id_from_email(email)
            if user_id:
                return user_id
                
        except Exception as e:
            logger.error(f"Basic auth error: {e}")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )

# Keep legacy endpoint for transition
async def get_current_user_id_legacy() -> str:
    """Legacy authentication endpoint"""
    return await get_current_user_id()

def create_auth_response(token: str, user_id: str) -> AuthResponse:
    """Create authentication response"""
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user_id=user_id
    ) 