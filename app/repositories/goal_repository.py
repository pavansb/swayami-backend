from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models import Goal, GoalCreate, GoalUpdate, GoalStatus
from app.database import get_database
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GoalRepository:
    def __init__(self):
        self.collection_name = "goals"
    
    def get_collection(self):
        db = get_database()
        return db[self.collection_name]
    
    async def create_goal(self, user_id: str, goal_data: GoalCreate) -> Goal:
        """Create a new goal"""
        goal_dict = goal_data.model_dump()
        goal_dict["user_id"] = user_id
        goal_dict["status"] = GoalStatus.ACTIVE
        goal_dict["progress"] = 0.0
        goal_dict["created_at"] = datetime.utcnow()
        goal_dict["updated_at"] = datetime.utcnow()
        
        collection = self.get_collection()
        result = await collection.insert_one(goal_dict)
        goal_dict["_id"] = str(result.inserted_id)
        
        return Goal(**goal_dict)
    
    async def get_goal_by_id(self, goal_id: str, user_id: str) -> Optional[Goal]:
        """Get a goal by ID and user ID"""
        try:
            collection = self.get_collection()
            goal_data = await collection.find_one({
                "_id": ObjectId(goal_id),
                "user_id": user_id
            })
            
            if goal_data:
                goal_data["_id"] = str(goal_data["_id"])
                return Goal(**goal_data)
            return None
        except Exception as e:
            logger.error(f"Error getting goal by ID: {e}")
            return None
    
    async def get_goals_by_user(
        self, 
        user_id: str, 
        status: Optional[GoalStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Goal]:
        """Get goals for a user with optional filtering"""
        try:
            query = {"user_id": user_id}
            if status:
                query["status"] = status.value
            
            collection = self.get_collection()
            cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            
            goals = []
            async for goal_data in cursor:
                goal_data["_id"] = str(goal_data["_id"])
                goals.append(Goal(**goal_data))
            
            return goals
        except Exception as e:
            logger.error(f"Error getting goals by user: {e}")
            return []
    
    async def update_goal(
        self, 
        goal_id: str, 
        user_id: str, 
        update_data: GoalUpdate
    ) -> Optional[Goal]:
        """Update a goal"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            if not update_dict:
                return await self.get_goal_by_id(goal_id, user_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            collection = self.get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(goal_id), "user_id": user_id},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_goal_by_id(goal_id, user_id)
            return None
        except Exception as e:
            logger.error(f"Error updating goal: {e}")
            return None
    
    async def update_goal_progress(
        self, 
        goal_id: str, 
        user_id: str, 
        progress: float
    ) -> Optional[Goal]:
        """Update goal progress percentage"""
        try:
            collection = self.get_collection()
            update_data = {
                "progress": max(0.0, min(100.0, progress)),  # Clamp between 0-100
                "updated_at": datetime.utcnow()
            }
            
            # If progress is 100%, mark as completed
            if progress >= 100.0:
                update_data["status"] = GoalStatus.COMPLETED.value
            
            result = await collection.update_one(
                {"_id": ObjectId(goal_id), "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_goal_by_id(goal_id, user_id)
            return None
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}")
            return None
    
    async def delete_goal(self, goal_id: str, user_id: str) -> bool:
        """Delete a goal"""
        try:
            collection = self.get_collection()
            result = await collection.delete_one({
                "_id": ObjectId(goal_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting goal: {e}")
            return False
    
    async def get_goals_by_category(self, user_id: str, category: str) -> List[Goal]:
        """Get goals by category"""
        try:
            collection = self.get_collection()
            cursor = collection.find({
                "user_id": user_id,
                "category": category
            }).sort("created_at", -1)
            
            goals = []
            async for goal_data in cursor:
                goal_data["_id"] = str(goal_data["_id"])
                goals.append(Goal(**goal_data))
            
            return goals
        except Exception as e:
            logger.error(f"Error getting goals by category: {e}")
            return []

# Singleton instance
goal_repository = GoalRepository() 