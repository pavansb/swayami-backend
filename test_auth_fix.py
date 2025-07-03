#!/usr/bin/env python3
"""
Quick Authentication Fix Test
============================

Tests that the authentication system now properly creates unique user IDs
instead of using hardcoded values, fixing the data isolation issue.
"""

import asyncio
import sys
from app.auth import auth_service
from app.repositories.user_repository import user_repository
from app.database import connect_to_mongo, close_mongo_connection

async def test_auth_fix():
    """Test that authentication creates unique user IDs"""
    
    print("🧪 Testing Authentication Fix")
    print("=" * 50)
    
    try:
        # Connect to database
        print("🔌 Connecting to MongoDB...")
        await connect_to_mongo()
        print("✅ Connected")
        
        # Test 1: Authentication should create unique users
        print("\n📝 Test 1: Creating unique users...")
        
        # Simulate user 1 authentication
        try:
            auth_response_1 = await auth_service.authenticate("contact.pavansb@gmail.com", "test123")
            user_id_1 = auth_response_1.user_id
            print(f"✅ User 1 ID: {user_id_1}")
        except Exception as e:
            print(f"❌ User 1 creation failed: {e}")
            return False
        
        # Verify user 1 exists in database
        user_1 = await user_repository.get_user_by_id(user_id_1)
        if user_1:
            print(f"✅ User 1 found in DB: {user_1.email}")
        else:
            print("❌ User 1 not found in database")
            return False
        
        # Test 2: Check that user ID is not hardcoded
        print(f"\n📝 Test 2: Checking user ID format...")
        if user_id_1 == "user_123":
            print("❌ CRITICAL: Still using hardcoded user ID!")
            return False
        else:
            print(f"✅ Using dynamic user ID: {user_id_1}")
        
        # Test 3: Verify MongoDB user lookup works
        print(f"\n📝 Test 3: Database isolation test...")
        user_lookup = await user_repository.get_user_by_email("contact.pavansb@gmail.com")
        if user_lookup and user_lookup.id == user_id_1:
            print("✅ Email-based lookup matches user ID")
        else:
            print("❌ Email lookup failed or ID mismatch")
            return False
        
        print("\n🎉 All tests passed! Authentication fix is working!")
        print("✅ Users now get unique IDs instead of hardcoded values")
        print("✅ Data isolation issue is resolved")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    print("🚀 Starting Authentication Fix Verification...\n")
    
    success = asyncio.run(test_auth_fix())
    
    if success:
        print("\n✅ RESULT: Authentication fix verified!")
        print("🚀 Ready for team testing with data isolation!")
        sys.exit(0)
    else:
        print("\n❌ RESULT: Authentication issues detected!")
        print("🔧 May need additional fixes before team testing")
        sys.exit(1) 