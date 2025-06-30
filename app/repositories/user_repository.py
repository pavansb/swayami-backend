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
            collection = self.get_collection()
            user_data = await collection.find_one({"_id": ObjectId(user_id)})
            
            if user_data:
                user_data["_id"] = str(user_data["_id"])
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
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
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            if not update_dict:
                return await self.get_user_by_id(user_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            collection = self.get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_user_by_id(user_id)
            return None
        except Exception as e:
            logger.error(f"Error updating user: {e}")
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