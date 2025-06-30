from fastapi import APIRouter, HTTPException, Depends
from app.models import MockAuthRequest, AuthResponse, User
from app.auth import auth_service, get_current_user_id
from app.repositories.user_repository import user_repository

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=AuthResponse)
async def login(auth_request: MockAuthRequest):
    """
    Mock authentication endpoint for development
    Email: contact.pavansb@gmail.com
    Password: test123
    """
    try:
        response = auth_service.authenticate(auth_request.email, auth_request.password)
        
        # Ensure user exists in database
        existing_user = await user_repository.get_user_by_email(auth_request.email)
        if not existing_user:
            # Create user if doesn't exist
            from app.models import UserCreate, Theme
            user_data = UserCreate(
                email=auth_request.email,
                name="Pavan SB",
                theme=Theme.SYSTEM
            )
            await user_repository.create_user(user_data)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@router.get("/me", response_model=User)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """Get current user information"""
    user = await user_repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/status")
async def auth_status(user_id: str = Depends(get_current_user_id)):
    """Check authentication status"""
    return {
        "authenticated": True,
        "user_id": user_id,
        "message": "Authentication successful"
    }

@router.post("/logout")
async def logout():
    """Mock logout endpoint"""
    return {"message": "Logged out successfully"}

@router.get("/test")
async def test_auth():
    """Test endpoint that doesn't require authentication"""
    return {
        "message": "Authentication system is working",
        "instructions": {
            "login": "POST /api/auth/login with email: contact.pavansb@gmail.com, password: test123",
            "bearer_token": "Use the returned access_token in Authorization header: 'Bearer <token>'",
            "basic_auth": "Or use Basic auth with base64(email:password)",
            "headers": "Authorization: Basic Y29udGFjdC5wYXZhbnNiQGdtYWlsLmNvbTp0ZXN0MTIz"
        }
    } 