from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models import Journal, JournalCreate, JournalUpdate
from app.database import get_database
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class JournalRepository:
    def __init__(self):
        self.collection_name = "journals"
    
    def get_collection(self):
        db = get_database()
        return db[self.collection_name]
    
    async def create_journal(self, user_id: str, journal_data: JournalCreate) -> Journal:
        """Create a new journal entry"""
        journal_dict = journal_data.model_dump()
        journal_dict["user_id"] = user_id
        journal_dict["created_at"] = datetime.utcnow()
        journal_dict["updated_at"] = datetime.utcnow()
        
        collection = self.get_collection()
        result = await collection.insert_one(journal_dict)
        journal_dict["_id"] = str(result.inserted_id)
        
        return Journal(**journal_dict)
    
    async def get_journal_by_id(self, journal_id: str, user_id: str) -> Optional[Journal]:
        """Get a journal entry by ID and user ID"""
        try:
            collection = self.get_collection()
            journal_data = await collection.find_one({
                "_id": ObjectId(journal_id),
                "user_id": user_id
            })
            
            if journal_data:
                journal_data["_id"] = str(journal_data["_id"])
                return Journal(**journal_data)
            return None
        except Exception as e:
            logger.error(f"Error getting journal by ID: {e}")
            return None
    
    async def get_journals_by_user(
        self, 
        user_id: str,
        days_back: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Journal]:
        """Get journal entries for a user with optional date filtering"""
        try:
            query = {"user_id": user_id}
            
            if days_back:
                start_date = datetime.utcnow() - timedelta(days=days_back)
                query["created_at"] = {"$gte": start_date}
            
            collection = self.get_collection()
            cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            
            journals = []
            async for journal_data in cursor:
                journal_data["_id"] = str(journal_data["_id"])
                journals.append(Journal(**journal_data))
            
            return journals
        except Exception as e:
            logger.error(f"Error getting journals by user: {e}")
            return []
    
    async def get_recent_journals(self, user_id: str, limit: int = 10) -> List[Journal]:
        """Get recent journal entries for a user"""
        try:
            collection = self.get_collection()
            cursor = collection.find({
                "user_id": user_id
            }).sort("created_at", -1).limit(limit)
            
            journals = []
            async for journal_data in cursor:
                journal_data["_id"] = str(journal_data["_id"])
                journals.append(Journal(**journal_data))
            
            return journals
        except Exception as e:
            logger.error(f"Error getting recent journals: {e}")
            return []
    
    async def update_journal(
        self, 
        journal_id: str, 
        user_id: str, 
        update_data: JournalUpdate
    ) -> Optional[Journal]:
        """Update a journal entry"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            if not update_dict:
                return await self.get_journal_by_id(journal_id, user_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            collection = self.get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(journal_id), "user_id": user_id},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_journal_by_id(journal_id, user_id)
            return None
        except Exception as e:
            logger.error(f"Error updating journal: {e}")
            return None
    
    async def update_ai_analysis(
        self, 
        journal_id: str, 
        user_id: str,
        ai_summary: str,
        sentiment_score: float
    ) -> Optional[Journal]:
        """Update journal with AI analysis results"""
        try:
            update_data = {
                "summary": ai_summary,
                "sentiment_score": sentiment_score,
                "updated_at": datetime.utcnow()
            }
            
            collection = self.get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(journal_id), "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_journal_by_id(journal_id, user_id)
            return None
        except Exception as e:
            logger.error(f"Error updating AI analysis: {e}")
            return None
    
    async def delete_journal(self, journal_id: str, user_id: str) -> bool:
        """Delete a journal entry"""
        try:
            collection = self.get_collection()
            result = await collection.delete_one({
                "_id": ObjectId(journal_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting journal: {e}")
            return False
    
    async def get_journals_by_date_range(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Journal]:
        """Get journal entries within a specific date range"""
        try:
            collection = self.get_collection()
            cursor = collection.find({
                "user_id": user_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("created_at", -1)
            
            journals = []
            async for journal_data in cursor:
                journal_data["_id"] = str(journal_data["_id"])
                journals.append(Journal(**journal_data))
            
            return journals
        except Exception as e:
            logger.error(f"Error getting journals by date range: {e}")
            return []
    
    async def search_journals(
        self, 
        user_id: str, 
        search_term: str,
        limit: int = 50
    ) -> List[Journal]:
        """Search journal entries by content"""
        try:
            collection = self.get_collection()
            cursor = collection.find({
                "user_id": user_id,
                "$text": {"$search": search_term}
            }).sort("created_at", -1).limit(limit)
            
            journals = []
            async for journal_data in cursor:
                journal_data["_id"] = str(journal_data["_id"])
                journals.append(Journal(**journal_data))
            
            return journals
        except Exception as e:
            logger.error(f"Error searching journals: {e}")
            # Fallback to regex search if text index doesn't exist
            try:
                cursor = collection.find({
                    "user_id": user_id,
                    "$or": [
                        {"title": {"$regex": search_term, "$options": "i"}},
                        {"content": {"$regex": search_term, "$options": "i"}}
                    ]
                }).sort("created_at", -1).limit(limit)
                
                journals = []
                async for journal_data in cursor:
                    journal_data["_id"] = str(journal_data["_id"])
                    journals.append(Journal(**journal_data))
                
                return journals
            except Exception as e2:
                logger.error(f"Error in fallback journal search: {e2}")
                return []

# Singleton instance
journal_repository = JournalRepository() 