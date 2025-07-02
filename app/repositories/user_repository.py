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
        user_dict = user_data.dict()  # Fixed: Pydantic v1 compatibility
        
        # Handle name/full_name mapping for production compatibility
        if user_dict.get("full_name") and not user_dict.get("name"):
            user_dict["name"] = user_dict["full_name"]
        elif not user_dict.get("name") and not user_dict.get("full_name"):
            # Fallback to email prefix if no name provided
            user_dict["name"] = user_dict.get("email", "").split("@")[0] or "User"
            
        # Ensure we have required fields
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        user_dict["has_completed_onboarding"] = False
        user_dict["streak"] = 0
        user_dict["level"] = "Mindful Novice"
        
        collection = self.get_collection()
        result = await collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        
        return User(**user_dict)
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID - ObjectId first approach (WORKING VERSION)"""
        try:
            logger.info(f"🔍 Looking up user by ID: {user_id}")
            collection = self.get_collection()
            
            # Try as ObjectId first (this was working)
            try:
                object_id = ObjectId(user_id)
                logger.info(f"🔍 Querying as ObjectId: {object_id}")
                user_data = await collection.find_one({"_id": object_id})
                logger.info(f"🔍 MongoDB query as ObjectId result: {user_data is not None}")
                
                if user_data:
                    user_data["_id"] = str(user_data["_id"])
                    logger.info(f"✅ User found via ObjectId: {user_data['_id']}")
                    return User(**user_data)
                    
            except Exception as oid_error:
                logger.warning(f"⚠️ ObjectId query failed: {oid_error}")
            
            # Fallback: Try as string _id
            logger.info(f"🔍 Fallback: Querying as string _id: {user_id}")
            user_data = await collection.find_one({"_id": user_id})
            logger.info(f"🔍 MongoDB query as string result: {user_data is not None}")
            
            if user_data:
                user_data["_id"] = str(user_data["_id"])
                logger.info(f"✅ User found via string _id: {user_data['_id']}")
                return User(**user_data)
            
            logger.warning(f"⚠️ No user found for ID: {user_id}")
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
        """Update a user - simplified string-first approach"""
        try:
            logger.info(f"🔄 Updating user ID: {user_id}")
            logger.info(f"🔄 Update data: {update_data}")
            
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}  # Fixed: Pydantic v1 compatibility
            if not update_dict:
                logger.info(f"📝 No fields to update, returning existing user")
                return await self.get_user_by_id(user_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            logger.info(f"📝 Final update dict: {update_dict}")
            
            collection = self.get_collection()
            
            # Try updating with string _id first (most likely case)
            logger.info(f"🔄 Updating with string _id: {user_id}")
            result = await collection.update_one(
                {"_id": user_id},
                {"$set": update_dict}
            )
            logger.info(f"📝 MongoDB update as string - matched: {result.matched_count}, modified: {result.modified_count}")
            
            if result.matched_count > 0:
                logger.info(f"✅ User updated via string _id")
                # Return the updated user directly without another lookup to avoid recursion
                updated_user_data = await collection.find_one({"_id": user_id})
                if updated_user_data:
                    updated_user_data["_id"] = str(updated_user_data["_id"])
                    return User(**updated_user_data)
                else:
                    logger.warning(f"⚠️ Updated user not found on retrieval")
                    return None
            
            # Fallback: Try updating with ObjectId
            try:
                object_id = ObjectId(user_id)
                logger.info(f"🔄 Fallback: Updating with ObjectId: {object_id}")
                result = await collection.update_one(
                    {"_id": object_id},
                    {"$set": update_dict}
                )
                logger.info(f"📝 MongoDB update as ObjectId - matched: {result.matched_count}, modified: {result.modified_count}")
                
                if result.matched_count > 0:
                    logger.info(f"✅ User updated via ObjectId fallback")
                    # Return the updated user directly
                    updated_user_data = await collection.find_one({"_id": object_id})
                    if updated_user_data:
                        updated_user_data["_id"] = str(updated_user_data["_id"])
                        return User(**updated_user_data)
                    
            except Exception as oid_error:
                logger.warning(f"⚠️ ObjectId update fallback failed: {oid_error}")
            
            logger.warning(f"⚠️ No user found to update for ID: {user_id}")
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