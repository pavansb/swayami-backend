#!/usr/bin/env python3
"""
Database Cleanup Script for Swayami Development
Clears all collections for fresh user testing
"""

import os
import sys
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

# Load environment variables
load_dotenv()

async def clean_database():
    """Clean all collections in the database"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    print("🧹 Starting database cleanup...")
    print(f"📊 Database: {settings.MONGODB_DB_NAME}")
    print(f"🔗 Connection: {settings.MONGODB_URL}")
    
    # Collections to clean
    collections_to_clean = [
        'users',
        'goals', 
        'tasks',
        'journals',
        'ai_logs',
        'sessions',
        'quotes'
    ]
    
    total_deleted = 0
    
    for collection_name in collections_to_clean:
        try:
            collection = db[collection_name]
            
            # Count documents before deletion
            count_before = await collection.count_documents({})
            
            if count_before > 0:
                # Delete all documents in the collection
                result = await collection.delete_many({})
                deleted_count = result.deleted_count
                total_deleted += deleted_count
                
                print(f"✅ {collection_name}: Deleted {deleted_count} documents")
            else:
                print(f"ℹ️  {collection_name}: No documents to delete")
                
        except Exception as e:
            print(f"❌ Error cleaning {collection_name}: {str(e)}")
    
    print(f"\n🎉 Database cleanup completed!")
    print(f"📈 Total documents deleted: {total_deleted}")
    print(f"🗄️  Collections cleaned: {len(collections_to_clean)}")
    
    # Close the connection
    client.close()
    
    return total_deleted

async def main():
    """Main function"""
    print("=" * 50)
    print("🧹 SWAYAMI DATABASE CLEANUP SCRIPT")
    print("=" * 50)
    print()
    
    # Confirm before proceeding
    confirm = input("⚠️  This will DELETE ALL DATA from the database. Are you sure? (yes/no): ")
    
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Cleanup cancelled by user")
        return
    
    # Double confirmation for safety
    confirm2 = input("🔴 Type 'DELETE' to confirm: ")
    
    if confirm2 != 'DELETE':
        print("❌ Cleanup cancelled - incorrect confirmation")
        return
    
    try:
        deleted_count = await clean_database()
        
        if deleted_count > 0:
            print(f"\n✅ Successfully cleaned {deleted_count} documents from the database")
            print("🆕 The database is now ready for fresh user testing")
        else:
            print("\nℹ️  Database was already empty")
            
    except Exception as e:
        print(f"\n❌ Database cleanup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 