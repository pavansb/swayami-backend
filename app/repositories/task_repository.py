from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models import Task, TaskCreate, TaskUpdate, TaskStatus
from app.database import get_database
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TaskRepository:
    def __init__(self):
        self.collection_name = "tasks"
    
    def get_collection(self):
        db = get_database()
        return db[self.collection_name]
    
    async def create_task(self, user_id: str, task_data: TaskCreate) -> Task:
        """Create a new task"""
        task_dict = task_data.model_dump()
        task_dict["user_id"] = user_id
        task_dict["status"] = TaskStatus.PENDING
        task_dict["is_ai_generated"] = False
        task_dict["created_at"] = datetime.utcnow()
        task_dict["updated_at"] = datetime.utcnow()
        
        collection = self.get_collection()
        result = await collection.insert_one(task_dict)
        task_dict["_id"] = str(result.inserted_id)
        
        return Task(**task_dict)
    
    async def create_ai_task(self, user_id: str, task_data: TaskCreate) -> Task:
        """Create a new AI-generated task"""
        task_dict = task_data.model_dump()
        task_dict["user_id"] = user_id
        task_dict["status"] = TaskStatus.PENDING
        task_dict["is_ai_generated"] = True
        task_dict["created_at"] = datetime.utcnow()
        task_dict["updated_at"] = datetime.utcnow()
        
        collection = self.get_collection()
        result = await collection.insert_one(task_dict)
        task_dict["_id"] = str(result.inserted_id)
        
        return Task(**task_dict)
    
    async def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get a task by ID and user ID"""
        try:
            collection = self.get_collection()
            task_data = await collection.find_one({
                "_id": ObjectId(task_id),
                "user_id": user_id
            })
            
            if task_data:
                task_data["_id"] = str(task_data["_id"])
                return Task(**task_data)
            return None
        except Exception as e:
            logger.error(f"Error getting task by ID: {e}")
            return None
    
    async def get_tasks_by_user(
        self, 
        user_id: str, 
        status: Optional[TaskStatus] = None,
        goal_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """Get tasks for a user with optional filtering"""
        try:
            query = {"user_id": user_id}
            if status:
                query["status"] = status.value
            if goal_id:
                query["goal_id"] = goal_id
            
            collection = self.get_collection()
            cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            
            tasks = []
            async for task_data in cursor:
                task_data["_id"] = str(task_data["_id"])
                tasks.append(Task(**task_data))
            
            return tasks
        except Exception as e:
            logger.error(f"Error getting tasks by user: {e}")
            return []
    
    async def get_tasks_by_goal(self, goal_id: str, user_id: str) -> List[Task]:
        """Get all tasks for a specific goal"""
        try:
            collection = self.get_collection()
            cursor = collection.find({
                "goal_id": goal_id,
                "user_id": user_id
            }).sort("created_at", -1)
            
            tasks = []
            async for task_data in cursor:
                task_data["_id"] = str(task_data["_id"])
                tasks.append(Task(**task_data))
            
            return tasks
        except Exception as e:
            logger.error(f"Error getting tasks by goal: {e}")
            return []
    
    async def update_task(
        self, 
        task_id: str, 
        user_id: str, 
        update_data: TaskUpdate
    ) -> Optional[Task]:
        """Update a task"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            if not update_dict:
                return await self.get_task_by_id(task_id, user_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            # If status is being set to completed, set completed_at timestamp
            if update_dict.get("status") == TaskStatus.COMPLETED.value:
                update_dict["completed_at"] = datetime.utcnow()
            
            collection = self.get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(task_id), "user_id": user_id},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_task_by_id(task_id, user_id)
            return None
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return None
    
    async def mark_task_completed(
        self, 
        task_id: str, 
        user_id: str,
        actual_duration: Optional[int] = None
    ) -> Optional[Task]:
        """Mark a task as completed"""
        try:
            update_data = {
                "status": TaskStatus.COMPLETED.value,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if actual_duration is not None:
                update_data["actual_duration"] = actual_duration
            
            collection = self.get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(task_id), "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_task_by_id(task_id, user_id)
            return None
        except Exception as e:
            logger.error(f"Error marking task completed: {e}")
            return None
    
    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task"""
        try:
            collection = self.get_collection()
            result = await collection.delete_one({
                "_id": ObjectId(task_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False
    
    async def get_pending_tasks(self, user_id: str, limit: int = 10) -> List[Task]:
        """Get pending tasks for today's recommendations"""
        try:
            collection = self.get_collection()
            cursor = collection.find({
                "user_id": user_id,
                "status": TaskStatus.PENDING.value
            }).sort([("priority", -1), ("created_at", 1)]).limit(limit)
            
            tasks = []
            async for task_data in cursor:
                task_data["_id"] = str(task_data["_id"])
                tasks.append(Task(**task_data))
            
            return tasks
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []

# Singleton instance
task_repository = TaskRepository() 