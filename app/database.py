from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

database = Database()

async def connect_to_mongo():
    """Create database connection and initialize collections"""
    try:
        database.client = AsyncIOMotorClient(settings.mongodb_uri)
        database.database = database.client[settings.database_name]
        
        # Test the connection
        await database.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB Atlas: {settings.database_name}")
        
        # Initialize collections with schemas and indexes
        await initialize_collections()
        
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()
        logger.info("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return database.database

async def initialize_collections():
    """Initialize MongoDB collections with schemas and indexes"""
    db = database.database
    
    try:
        # Users collection
        await create_collection_with_schema(db, "users", {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["email", "name", "created_at"],
                "properties": {
                    "email": {"bsonType": "string", "pattern": "^.+@.+$"},
                    "name": {"bsonType": "string", "minLength": 1},
                    "theme": {"enum": ["light", "dark", "system"]},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        })
        await db.users.create_index("email", unique=True)
        
        # Goals collection
        await create_collection_with_schema(db, "goals", {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "title", "status", "priority", "progress", "created_at"],
                "properties": {
                    "user_id": {"bsonType": "string"},
                    "title": {"bsonType": "string", "minLength": 1, "maxLength": 200},
                    "description": {"bsonType": ["string", "null"], "maxLength": 1000},
                    "category": {"bsonType": ["string", "null"], "maxLength": 50},
                    "status": {"enum": ["active", "completed", "paused", "archived"]},
                    "priority": {"enum": ["low", "medium", "high"]},
                    "progress": {"bsonType": "number", "minimum": 0, "maximum": 100},
                    "target_date": {"bsonType": ["date", "null"]},
                    "tags": {"bsonType": "array", "items": {"bsonType": "string"}},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        })
        await db.goals.create_index([("user_id", 1), ("status", 1)])
        await db.goals.create_index([("user_id", 1), ("category", 1)])
        await db.goals.create_index([("user_id", 1), ("created_at", -1)])
        
        # Tasks collection
        await create_collection_with_schema(db, "tasks", {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "title", "status", "priority", "created_at"],
                "properties": {
                    "user_id": {"bsonType": "string"},
                    "goal_id": {"bsonType": ["string", "null"]},
                    "title": {"bsonType": "string", "minLength": 1, "maxLength": 200},
                    "description": {"bsonType": ["string", "null"], "maxLength": 1000},
                    "status": {"enum": ["pending", "in_progress", "completed", "cancelled"]},
                    "priority": {"enum": ["low", "medium", "high"]},
                    "is_ai_generated": {"bsonType": "bool"},
                    "estimated_duration": {"bsonType": ["int", "null"], "minimum": 1},
                    "actual_duration": {"bsonType": ["int", "null"], "minimum": 1},
                    "due_date": {"bsonType": ["date", "null"]},
                    "completed_at": {"bsonType": ["date", "null"]},
                    "tags": {"bsonType": "array", "items": {"bsonType": "string"}},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        })
        await db.tasks.create_index([("user_id", 1), ("status", 1)])
        await db.tasks.create_index([("user_id", 1), ("goal_id", 1)])
        await db.tasks.create_index([("user_id", 1), ("due_date", 1)])
        await db.tasks.create_index([("user_id", 1), ("priority", 1), ("status", 1)])
        
        # Journals collection
        await create_collection_with_schema(db, "journals", {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "content", "created_at"],
                "properties": {
                    "user_id": {"bsonType": "string"},
                    "title": {"bsonType": ["string", "null"], "maxLength": 200},
                    "content": {"bsonType": "string", "minLength": 1, "maxLength": 5000},
                    "mood_score": {"bsonType": ["int", "null"], "minimum": 1, "maximum": 5},
                    "summary": {"bsonType": ["string", "null"], "maxLength": 1000},
                    "sentiment_score": {"bsonType": ["number", "null"], "minimum": -1, "maximum": 1},
                    "tags": {"bsonType": "array", "items": {"bsonType": "string"}},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        })
        await db.journals.create_index([("user_id", 1), ("created_at", -1)])
        await db.journals.create_index([("user_id", 1), ("mood_score", 1)])
        # Text index for search functionality
        await db.journals.create_index([("title", "text"), ("content", "text")])
        
        # AI Logs collection
        await create_collection_with_schema(db, "ai_logs", {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "type", "input", "output", "timestamp"],
                "properties": {
                    "user_id": {"bsonType": "string"},
                    "type": {"enum": ["task_generation", "journal_summary", "mood_analysis", "recommendations"]},
                    "input": {"bsonType": "object"},
                    "output": {"bsonType": "object"},
                    "timestamp": {"bsonType": "date"}
                }
            }
        })
        await db.ai_logs.create_index([("user_id", 1), ("timestamp", -1)])
        await db.ai_logs.create_index([("user_id", 1), ("type", 1)])
        
        # Quotes collection
        await create_collection_with_schema(db, "quotes", {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["text", "author", "created_at"],
                "properties": {
                    "text": {"bsonType": "string", "minLength": 1, "maxLength": 500},
                    "author": {"bsonType": "string", "minLength": 1, "maxLength": 100},
                    "created_at": {"bsonType": "date"}
                }
            }
        })
        await db.quotes.create_index("author")
        
        # Sessions collection
        await create_collection_with_schema(db, "sessions", {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "start_time", "created_at"],
                "properties": {
                    "user_id": {"bsonType": "string"},
                    "start_time": {"bsonType": "date"},
                    "end_time": {"bsonType": ["date", "null"]},
                    "actions": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["action", "timestamp"],
                            "properties": {
                                "action": {"bsonType": "string"},
                                "timestamp": {"bsonType": "date"},
                                "data": {"bsonType": ["object", "null"]}
                            }
                        }
                    },
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        })
        await db.sessions.create_index([("user_id", 1), ("start_time", -1)])
        
        logger.info("✅ All collections initialized with schemas and indexes")
        
    except Exception as e:
        logger.error(f"Error initializing collections: {e}")
        # Don't raise - allow app to continue even if schema creation fails

async def create_collection_with_schema(db, collection_name: str, schema: dict):
    """Create collection with JSON schema validation"""
    try:
        # Check if collection exists
        collections = await db.list_collection_names()
        if collection_name not in collections:
            await db.create_collection(collection_name, validator=schema)
            logger.info(f"✅ Created collection: {collection_name}")
        else:
            # Update schema for existing collection
            try:
                await db.command("collMod", collection_name, validator=schema)
                logger.info(f"🔄 Updated schema for collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Could not update schema for {collection_name}: {e}")
    except Exception as e:
        logger.error(f"Error creating collection {collection_name}: {e}")

async def seed_initial_data():
    """Seed initial data like quotes"""
    db = database.database
    
    try:
        # Check if quotes collection is empty
        quote_count = await db.quotes.count_documents({})
        if quote_count == 0:
            initial_quotes = [
                {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
                {"text": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"},
                {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
                {"text": "It is during our darkest moments that we must focus to see the light.", "author": "Aristotle"},
                {"text": "Your limitation—it's only your imagination.", "author": "Unknown"},
                {"text": "Push yourself, because no one else is going to do it for you.", "author": "Unknown"},
                {"text": "Great things never come from comfort zones.", "author": "Unknown"},
                {"text": "Dream it. Wish it. Do it.", "author": "Unknown"},
                {"text": "Success doesn't just find you. You have to go out and get it.", "author": "Unknown"},
                {"text": "The harder you work for something, the greater you'll feel when you achieve it.", "author": "Unknown"}
            ]
            
            from datetime import datetime
            for quote in initial_quotes:
                quote["created_at"] = datetime.utcnow()
            
            await db.quotes.insert_many(initial_quotes)
            logger.info(f"✅ Seeded {len(initial_quotes)} initial quotes")
            
    except Exception as e:
        logger.error(f"Error seeding initial data: {e}") 