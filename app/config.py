from pydantic import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # MongoDB Atlas connection
    mongodb_uri: str = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL", "mongodb+srv://contactpavansb:gMM6ZpQ7ysZ1K1QX@swayami-app-db.wyd3sts.mongodb.net/?retryWrites=true&w=majority&appName=swayami-app-db")
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
    
    # Brand Colors - Swayami Green Theme
    brand_primary_color: str = "#6FCC7F"  # Swayami Green
    brand_primary_hover: str = "#5bb96a"
    brand_primary_light: str = "#e8f5ea"
    brand_primary_dark: str = "#4a8f54"
    brand_accent_color: str = "#9650D4"  # Purple accent (kept for contrast)
    brand_success_color: str = "#6FCC7F"
    brand_error_color: str = "#e53e3e"
    brand_warning_color: str = "#d69e2e"
    brand_info_color: str = "#3182ce"
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields to prevent validation errors

settings = Settings() 