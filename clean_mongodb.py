import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def clean_all_collections():
    # Connect to MongoDB
    mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
    db = client.swayami_db
    
    collections_to_clean = ['users', 'goals', 'tasks', 'journals', 'sessions', 'ai_logs']
    
    print("🗑️ Cleaning MongoDB collections...")
    
    for collection_name in collections_to_clean:
        collection = db[collection_name]
        result = await collection.delete_many({})
        print(f"✅ Deleted {result.deleted_count} documents from {collection_name}")
    
    print("🎉 MongoDB cleanup complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(clean_all_collections())
