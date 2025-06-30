from fastapi import APIRouter, HTTPException, Depends
from app.models import User, UserCreate, UserUpdate
from app.auth import get_current_user_id, get_user_id_flexible
from app.repositories.user_repository import user_repository
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/by-email/{email}", response_model=User)
async def get_user_by_email(email: str):
    """
    Get user by email address
    This endpoint is used by the frontend during authentication flow
    """
    try:
        logger.info(f"🔍 Getting user by email: {email}")
        user = await user_repository.get_user_by_email(email)
        
        if not user:
            logger.warning(f"⚠️ User not found for email: {email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ User found: {user.id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user by email: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@router.get("/me", response_model=User)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """Get current authenticated user"""
    try:
        user = await user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(user_id: str):
    """Get user by ID"""
    try:
        user = await user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@router.post("/", response_model=User)
async def create_user(user_data: UserCreate):
    """
    Create a new user
    This endpoint is used during the user registration/onboarding process
    """
    try:
        logger.info(f"🔨 Creating new user: {user_data.email}")
        
        # Check if user already exists
        existing_user = await user_repository.get_user_by_email(user_data.email)
        if existing_user:
            logger.warning(f"⚠️ User already exists: {user_data.email}")
            raise HTTPException(status_code=409, detail="User with this email already exists")
        
        # Create new user
        user = await user_repository.create_user(user_data)
        logger.info(f"✅ User created successfully: {user.id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str, 
    update_data: UserUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update user (flexible auth for development)"""
    try:
        logger.info(f"🔐 UPDATE USER AUTH DEBUG:")
        logger.info(f"🔐 URL user_id: {user_id}")
        logger.info(f"🔐 Token user_id: {current_user_id}")
        logger.info(f"🔐 Update data: {update_data}")
        
        # In development mode with mock auth, allow updates
        # TODO: In production, enforce strict user ID matching
        if user_id != current_user_id:
            logger.warning(f"⚠️ USER ID MISMATCH - URL: {user_id}, Token: {current_user_id}")
            logger.warning(f"⚠️ ALLOWING UPDATE FOR DEVELOPMENT MODE")
        
        user = await user_repository.update_user(user_id, update_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        logger.info(f"✅ User updated successfully: {user.id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@router.put("/{user_id}/onboarding", response_model=User)
async def update_user_onboarding(
    user_id: str,
    onboarding_data: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update user onboarding status
    This endpoint is called when the user completes the onboarding process
    """
    try:
        logger.info(f"🎯 ONBOARDING UPDATE: user_id={user_id}, data={onboarding_data}")
        
        # In development mode with mock auth, allow updates
        if user_id != current_user_id:
            logger.warning(f"⚠️ ONBOARDING USER ID MISMATCH - URL: {user_id}, Token: {current_user_id}")
            logger.warning(f"⚠️ ALLOWING ONBOARDING UPDATE FOR DEVELOPMENT MODE")
        
        # Extract onboarding completion status
        has_completed_onboarding = onboarding_data.get('has_completed_onboarding', False)
        
        # Update user with onboarding status
        update_data = UserUpdate(has_completed_onboarding=has_completed_onboarding)
        user = await user_repository.update_user(user_id, update_data)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        logger.info(f"✅ User onboarding updated successfully: {user.id}, completed: {has_completed_onboarding}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating user onboarding: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating onboarding: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete user (users can only delete their own account)"""
    try:
        # Users can only delete their own account
        if user_id != current_user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own account")
        
        success = await user_repository.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@router.get("/email/{email}/exists")
async def check_user_exists(email: str):
    """
    Check if a user exists with the given email
    Returns boolean without exposing user data
    """
    try:
        user = await user_repository.get_user_by_email(email)
        return {"exists": user is not None, "email": email}
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking user: {str(e)}") 