#!/usr/bin/env python3
"""
Debug script to check what's actually stored in MongoDB for the user
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import json

async def debug_user():
    # Get MongoDB connection string from environment
    mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/swayami-dev')
    
    print(f"🔍 Connecting to MongoDB: {mongodb_url[:50]}...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_url)
    db = client.get_default_database()
    collection = db.users
    
    print("🔍 Checking all users in the collection...")
    
    # Get all users
    async for user in collection.find():
        print(f"\n📄 User document:")
        print(f"   _id: {user['_id']} (type: {type(user['_id'])})")
        print(f"   email: {user['email']}")
        print(f"   name: {user.get('name', 'N/A')}")
        print(f"   created_at: {user.get('created_at', 'N/A')}")
        
        # Check if _id is ObjectId or string
        if isinstance(user['_id'], ObjectId):
            print(f"   ✅ _id is proper ObjectId: {str(user['_id'])}")
        else:
            print(f"   ❌ _id is not ObjectId: {user['_id']} (type: {type(user['_id'])})")
    
    print(f"\n🔍 Testing specific user ID: 686297879a25b97b568c0908")
    
    # Test 1: Query as string
    user_by_string = await collection.find_one({"_id": "686297879a25b97b568c0908"})
    print(f"   Query as string: {'✅ Found' if user_by_string else '❌ Not found'}")
    
    # Test 2: Query as ObjectId
    try:
        object_id = ObjectId("686297879a25b97b568c0908")
        user_by_objectid = await collection.find_one({"_id": object_id})
        print(f"   Query as ObjectId: {'✅ Found' if user_by_objectid else '❌ Not found'}")
    except Exception as e:
        print(f"   Query as ObjectId: ❌ Error: {e}")
    
    # Test 3: Query by email
    user_by_email = await collection.find_one({"email": "contact.pavansb@gmail.com"})
    if user_by_email:
        print(f"   Query by email: ✅ Found")
        print(f"   Email result _id: {user_by_email['_id']} (type: {type(user_by_email['_id'])})")
    else:
        print(f"   Query by email: ❌ Not found")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(debug_user()) 