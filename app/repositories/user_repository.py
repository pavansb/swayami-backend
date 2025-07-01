from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models import User, UserCreate, UserUpdate
from app.database import get_database
from typing import Optional
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self):
        self.collection_name = "users"
    
    def get_collection(self):
        db = get_database()
        return db[self.collection_name]
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        user_dict = user_data.model_dump()
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        collection = self.get_collection()
        result = await collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        
        return User(**user_dict)
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        try:
            logger.info(f"🔍 Looking up user by ID: {user_id}")
            
            # Validate ObjectId format
            try:
                object_id = ObjectId(user_id)
                logger.info(f"✅ Valid ObjectId created: {object_id}")
            except Exception as oid_error:
                logger.error(f"❌ Invalid ObjectId format: {user_id}, error: {oid_error}")
                return None
            
            collection = self.get_collection()
            logger.info(f"🔍 Querying MongoDB collection: {self.collection_name}")
            
            user_data = await collection.find_one({"_id": object_id})
            logger.info(f"🔍 MongoDB query result: {user_data is not None}")
            
            if user_data:
                user_data["_id"] = str(user_data["_id"])
                logger.info(f"✅ User found and converted: {user_data['_id']}")
                return User(**user_data)
            else:
                logger.warning(f"⚠️ No user found in MongoDB for ObjectId: {object_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Unexpected error getting user by ID: {type(e).__name__}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        try:
            collection = self.get_collection()
            user_data = await collection.find_one({"email": email})
            
            if user_data:
                user_data["_id"] = str(user_data["_id"])
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[User]:
        """Update a user"""
        try:
            logger.info(f"🔄 Updating user ID: {user_id}")
            logger.info(f"🔄 Update data: {update_data}")
            
            # Validate ObjectId format first
            try:
                object_id = ObjectId(user_id)
                logger.info(f"✅ Valid ObjectId for update: {object_id}")
            except Exception as oid_error:
                logger.error(f"❌ Invalid ObjectId format for update: {user_id}, error: {oid_error}")
                return None
            
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            if not update_dict:
                logger.info(f"📝 No fields to update, returning existing user")
                return await self.get_user_by_id(user_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            logger.info(f"📝 Final update dict: {update_dict}")
            
            collection = self.get_collection()
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": update_dict}
            )
            
            logger.info(f"📝 MongoDB update result - matched: {result.matched_count}, modified: {result.modified_count}")
            
            if result.matched_count > 0:
                logger.info(f"✅ User found for update, retrieving updated user")
                return await self.get_user_by_id(user_id)
            else:
                logger.warning(f"⚠️ No user found to update with ObjectId: {object_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Unexpected error updating user: {type(e).__name__}: {e}")
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            collection = self.get_collection()
            result = await collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

# Singleton instance
user_repository = UserRepository() 