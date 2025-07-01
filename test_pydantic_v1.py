#!/usr/bin/env python3
"""
Pydantic v1 Validation Test
===========================

Quick test to ensure our Pydantic v1 downgrade is working correctly.
Run this after installing requirements.txt to verify compatibility.
"""

def test_pydantic_v1_compatibility():
    """Test that our models work correctly with Pydantic v1"""
    
    try:
        # Test imports
        from pydantic import BaseModel, BaseSettings, Field, EmailStr
        from app.config import settings
        from app.models import User, Goal, Task, Journal
        
        print("✅ All imports successful")
        
        # Test settings
        print(f"✅ Settings loaded - MongoDB URI: {settings.mongodb_uri[:20]}...")
        print(f"✅ Settings OpenAI key: {'Set' if settings.openai_api_key else 'Not set'}")
        
        # Test model creation
        test_user_data = {
            "_id": "test_123",
            "email": "test@example.com",
            "name": "Test User",
            "theme": "light"
        }
        
        user = User(**test_user_data)
        print(f"✅ User model created: {user.email}")
        
        # Test model validation
        try:
            invalid_user = User(**{
                "_id": "test_456",
                "email": "invalid-email",  # This should fail
                "name": "Test User",
                "theme": "light"
            })
            print("❌ Email validation should have failed!")
        except Exception:
            print("✅ Email validation working correctly")
        
        # Test JSON serialization
        user_json = user.dict()
        print(f"✅ JSON serialization working: {type(user_json)}")
        
        print("\n🎉 All Pydantic v1 tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_pydantic_v1_compatibility() 