from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum

class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ARCHIVED = "archived"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class MoodLevel(int, Enum):
    VERY_SAD = 1
    SAD = 2
    NEUTRAL = 3
    HAPPY = 4
    VERY_HAPPY = 5

class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

class AILogType(str, Enum):
    TASK_GENERATION = "task_generation"
    JOURNAL_SUMMARY = "journal_summary"
    MOOD_ANALYSIS = "mood_analysis"
    RECOMMENDATIONS = "recommendations"

# User Models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    theme: Theme = Theme.SYSTEM

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    theme: Optional[Theme] = None
    has_completed_onboarding: Optional[bool] = None

class User(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    has_completed_onboarding: bool = Field(default=False)
    
    class Config:
        populate_by_name = True

# Goal Models
class GoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    target_date: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    tags: List[str] = Field(default_factory=list)

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    target_date: Optional[datetime] = None
    priority: Optional[Priority] = None
    status: Optional[GoalStatus] = None
    tags: Optional[List[str]] = None

class Goal(GoalBase):
    id: str = Field(alias="_id")
    user_id: str
    status: GoalStatus = GoalStatus.ACTIVE
    progress: float = Field(default=0.0, ge=0, le=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

# Task Models
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Priority = Priority.MEDIUM
    estimated_duration: Optional[int] = Field(None, description="Duration in minutes")
    due_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)

class TaskCreate(TaskBase):
    goal_id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    estimated_duration: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    goal_id: Optional[str] = None

class Task(TaskBase):
    id: str = Field(alias="_id")
    user_id: str
    goal_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    is_ai_generated: bool = False
    actual_duration: Optional[int] = Field(None, description="Actual time spent in minutes")
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

# Journal Models
class JournalBase(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    mood_score: Optional[int] = Field(None, ge=1, le=5, description="Mood score 1-5")
    tags: List[str] = Field(default_factory=list)

class JournalCreate(JournalBase):
    pass

class JournalUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    mood_score: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = None

class Journal(JournalBase):
    id: str = Field(alias="_id")
    user_id: str
    summary: Optional[str] = Field(None, max_length=1000, description="AI-generated summary")
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

# AI Log Models
class AILogBase(BaseModel):
    type: AILogType
    input: Dict[str, Any] = Field(..., description="Input data for AI operation")
    output: Dict[str, Any] = Field(..., description="AI response data")

class AILogCreate(AILogBase):
    pass

class AILog(AILogBase):
    id: str = Field(alias="_id")
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

# Quote Models
class QuoteBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=100)

class QuoteCreate(QuoteBase):
    pass

class Quote(QuoteBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

# Session Models
class SessionAction(BaseModel):
    action: str = Field(..., description="Action performed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SessionBase(BaseModel):
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    actions: List[SessionAction] = Field(default_factory=list)

class SessionCreate(BaseModel):
    pass

class SessionUpdate(BaseModel):
    end_time: Optional[datetime] = None
    actions: Optional[List[SessionAction]] = None

class Session(SessionBase):
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

# AI Service Request/Response Models
class TaskGenerationRequest(BaseModel):
    goal_id: str
    user_preferences: Optional[dict] = Field(default_factory=dict)
    count: int = Field(default=5, ge=1, le=20)

class TaskGenerationResponse(BaseModel):
    tasks: List[TaskCreate]
    reasoning: Optional[str] = None

class JournalSummaryRequest(BaseModel):
    journal_id: str

class JournalSummaryResponse(BaseModel):
    summary: str
    key_themes: List[str]
    sentiment_score: float
    mood_analysis: str

class MoodAnalysisRequest(BaseModel):
    journal_ids: List[str]
    date_range_days: int = Field(default=7, ge=1, le=90)

class MoodAnalysisResponse(BaseModel):
    overall_sentiment: float
    mood_trend: str
    insights: List[str]
    recommendations: List[str]

# Authentication Models
class MockAuthRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    user_id: str
    email: str
    name: str
    access_token: str
    token_type: str = "bearer" 