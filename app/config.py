from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # MongoDB Atlas connection
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb+srv://contactpavansb:gMM6ZpQ7ysZ1K1QX@swayami-app-db.wyd3sts.mongodb.net/?retryWrites=true&w=majority&appName=swayami-app-db")
    database_name: str = os.getenv("DATABASE_NAME", "Swayami")
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Security Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Mock Auth for Development
    mock_auth_enabled: bool = os.getenv("MOCK_AUTH_ENABLED", "true").lower() == "true"
    mock_user_email: str = "contact.pavansb@gmail.com"
    mock_user_password: str = "test123"
    mock_user_id: str = "user_123"
    
    class Config:
        env_file = ".env"

settings = Settings() 