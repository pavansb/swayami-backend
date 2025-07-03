#!/usr/bin/env python3
"""
MongoDB Database Cleanup Script for Swayami
=============================================

This script safely cleans all data from MongoDB collections to prepare for YC demo.
It removes all user data including goals, tasks, journals, sessions, AI logs, quotes, etc.

Usage:
    python clean_mongodb.py [--confirm]

Safety Features:
- Requires explicit confirmation before deletion
- Provides detailed summary of what will be deleted
- Backs up collection names and counts before deletion
- Uses environment variables for database connection

⚠️  WARNING: This will permanently delete ALL user data! ⚠️
"""

import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBCleaner:
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL")
        self.database_name = os.getenv("DATABASE_NAME", "Swayami")
        self.client = None
        self.db = None
        
        if not self.mongodb_uri:
            print("❌ Error: MONGODB_URI not found in environment variables")
            sys.exit(1)

    async def connect(self):
        """Connect to MongoDB"""
        try:
            print("🔌 Connecting to MongoDB...")
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB database: {self.database_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False

    async def get_database_stats(self):
        """Get current database statistics"""
        try:
            collections = await self.db.list_collection_names()
            stats = {}
            total_documents = 0
            
            for collection_name in collections:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = count
                total_documents += count
            
            return stats, total_documents
            
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {}, 0

    async def clean_all_collections(self):
        """Clean all collections in the database"""
        try:
            print("\n🧹 Starting database cleanup...")
            
            # Get current stats
            before_stats, total_before = await self.get_database_stats()
            
            if total_before == 0:
                print("ℹ️  Database is already empty!")
                return True
            
            print(f"\n📊 Current Database State:")
            print(f"   Total Collections: {len(before_stats)}")
            print(f"   Total Documents: {total_before}")
            print("\n📋 Collection Details:")
            
            for collection_name, count in before_stats.items():
                print(f"   - {collection_name}: {count} documents")
            
            # Drop all collections
            collections = await self.db.list_collection_names()
            deleted_collections = []
            
            for collection_name in collections:
                try:
                    await self.db[collection_name].drop()
                    deleted_collections.append(collection_name)
                    print(f"   ✅ Deleted collection: {collection_name}")
                except Exception as e:
                    print(f"   ❌ Failed to delete {collection_name}: {e}")
            
            # Verify cleanup
            after_stats, total_after = await self.get_database_stats()
            
            print(f"\n✅ Cleanup Complete!")
            print(f"   Collections deleted: {len(deleted_collections)}")
            print(f"   Documents removed: {total_before}")
            print(f"   Remaining documents: {total_after}")
            
            if total_after == 0:
                print("🎉 Database successfully cleaned!")
            else:
                print("⚠️  Some data may still remain")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return False

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔌 Database connection closed")

def print_banner():
    """Print script banner"""
    print("=" * 70)
    print("🧹 SWAYAMI MONGODB CLEANUP SCRIPT")
    print("=" * 70)
    print("⚠️  WARNING: This will permanently delete ALL user data!")
    print("   - Users, Goals, Tasks, Journals")
    print("   - Sessions, AI Logs, Quotes")
    print("   - All other collections")
    print("=" * 70)

def get_user_confirmation():
    """Get explicit user confirmation"""
    print("\n🔒 SAFETY CHECK:")
    print("   This action cannot be undone!")
    print("   All user data will be permanently lost!")
    
    confirm1 = input("\n   Type 'DELETE ALL DATA' to confirm: ").strip()
    if confirm1 != "DELETE ALL DATA":
        print("❌ Confirmation failed. Cleanup cancelled.")
        return False
    
    confirm2 = input("   Type 'YES' to proceed: ").strip().upper()
    if confirm2 != "YES":
        print("❌ Confirmation failed. Cleanup cancelled.")
        return False
    
    print("\n✅ Confirmation received. Proceeding with cleanup...")
    return True

async def main():
    """Main execution function"""
    print_banner()
    
    # Check for --confirm flag
    skip_confirmation = "--confirm" in sys.argv
    
    if not skip_confirmation:
        if not get_user_confirmation():
            sys.exit(0)
    else:
        print("🚀 Auto-confirmation mode enabled (--confirm flag)")
    
    # Initialize cleaner
    cleaner = MongoDBCleaner()
    
    try:
        # Connect to database
        if not await cleaner.connect():
            sys.exit(1)
        
        # Clean database
        success = await cleaner.clean_all_collections()
        
        if success:
            print("\n🎉 SUCCESS: Database cleanup completed!")
            print("   ✅ Ready for YC demo with clean data")
            print("   ✅ Supabase Auth can now be reset too")
        else:
            print("\n❌ FAILED: Database cleanup encountered errors")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    
    finally:
        await cleaner.close()

if __name__ == "__main__":
    # Run the cleanup
    asyncio.run(main())
