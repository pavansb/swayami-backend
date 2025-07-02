from openai import OpenAI
from app.config import settings
from app.models import (
    Goal, Task, Journal, TaskCreate, TaskGenerationRequest, TaskGenerationResponse,
    JournalSummaryResponse, MoodAnalysisResponse, Priority
)
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.client = None
        self.is_configured = bool(self.api_key and self.api_key != "")
        
        if self.is_configured:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ OPENAI SERVICE: Successfully initialized with API key")
            except Exception as e:
                logger.error(f"❌ OPENAI SERVICE: Failed to initialize client: {e}")
                self.is_configured = False
        else:
            logger.warning("⚠️ OPENAI SERVICE: No API key provided - using fallback responses only")
    
    async def test_openai_connection(self) -> dict:
        """Test OpenAI API connection and return status"""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "OpenAI API key not provided",
                "api_key_set": bool(self.api_key)
            }
        
        try:
            # Simple test call
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello, respond with 'OpenAI is working!'"}],
                max_tokens=10
            )
            
            content = response.choices[0].message.content
            logger.info(f"✅ OPENAI SERVICE: Test successful - {content}")
            
            return {
                "status": "working",
                "message": "OpenAI API is working correctly",
                "test_response": content
            }
            
        except Exception as e:
            logger.error(f"❌ OPENAI SERVICE: Test failed - {e}")
            return {
                "status": "error", 
                "message": f"OpenAI API test failed: {str(e)}",
                "error": str(e)
            }
    
    async def generate_tasks_for_goal(
        self, 
        goal: Goal, 
        request: TaskGenerationRequest,
        existing_tasks: List[Task] = None
    ) -> TaskGenerationResponse:
        """Generate AI-powered tasks for a specific goal"""
        
        if not self.is_configured:
            logger.warning("🤖 OPENAI SERVICE: Using fallback tasks - OpenAI not configured")
            return self._generate_fallback_tasks(goal)
        
        try:
            logger.info(f"🤖 OPENAI SERVICE: Generating tasks for goal: {goal.title}")
            
            existing_tasks_summary = ""
            if existing_tasks:
                existing_tasks_summary = "\n".join([
                    f"- {task.title}: {task.status.value}" 
                    for task in existing_tasks[:10]  # Limit to avoid token overflow
                ])
            
            prompt = f"""
You are a productivity coach helping a user achieve their goal. Generate {request.count} actionable, specific tasks.

Goal Details:
- Title: {goal.title}
- Description: {goal.description or "No description provided"}
- Category: {goal.category or "General"}
- Priority: {goal.priority.value}
- Current Progress: {goal.progress}%
- Target Date: {goal.target_date.strftime('%Y-%m-%d') if goal.target_date else "No deadline"}

Existing Tasks (for context):
{existing_tasks_summary or "No existing tasks"}

User Preferences:
{json.dumps(request.user_preferences, indent=2) if request.user_preferences else "No specific preferences"}

Generate tasks that are:
1. Specific and actionable
2. Appropriately sized (not too big or too small)
3. Logically sequenced toward the goal
4. Varied in approach and skill requirements
5. Include estimated duration in minutes

Return your response as a JSON object with this exact structure:
{{
    "tasks": [
        {{
            "title": "Task title",
            "description": "Detailed description",
            "priority": "high|medium|low",
            "estimated_duration": 60,
            "tags": ["tag1", "tag2"]
        }}
    ],
    "reasoning": "Brief explanation of task selection and sequencing"
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful productivity coach. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ OPENAI SERVICE: Successfully generated {len(result.get('tasks', []))} tasks")
            
            # Convert to TaskCreate objects
            tasks = []
            for task_data in result.get("tasks", []):
                task = TaskCreate(
                    title=task_data["title"],
                    description=task_data.get("description", ""),
                    priority=Priority(task_data.get("priority", "medium")),
                    estimated_duration=task_data.get("estimated_duration"),
                    tags=task_data.get("tags", []),
                    goal_id=goal.id
                )
                tasks.append(task)
            
            return TaskGenerationResponse(
                tasks=tasks,
                reasoning=result.get("reasoning", "")
            )
            
        except Exception as e:
            logger.error(f"❌ OPENAI SERVICE: Task generation failed, using fallback: {e}")
            return self._generate_fallback_tasks(goal)
    
    def _generate_fallback_tasks(self, goal: Goal) -> TaskGenerationResponse:
        """Generate fallback tasks when OpenAI is not available"""
        fallback_tasks = [
            TaskCreate(
                title=f"Plan your approach to {goal.title}",
                description="Break down this goal into smaller, manageable steps",
                priority=goal.priority,
                estimated_duration=45,
                tags=["planning"],
                goal_id=goal.id
            ),
            TaskCreate(
                title=f"Research strategies for {goal.title}",
                description="Look up best practices and methods to achieve this goal",
                priority=Priority.MEDIUM,
                estimated_duration=60,
                tags=["research"],
                goal_id=goal.id
            ),
            TaskCreate(
                title=f"Take first action toward {goal.title}",
                description=goal.description or "Start with the most obvious first step",
                priority=goal.priority,
                estimated_duration=30,
                tags=["action"],
                goal_id=goal.id
            )
        ]
        return TaskGenerationResponse(
            tasks=fallback_tasks,
            reasoning="Generated fallback tasks - OpenAI API not available"
        )
    
    async def generate_smart_tasks_from_goal_description(
        self, 
        goal_title: str, 
        goal_description: str
    ) -> dict:
        """Generate smart tasks from goal title and description (for frontend API)"""
        
        if not self.is_configured:
            logger.warning("🤖 OPENAI SERVICE: Using fallback tasks - OpenAI not configured")
            return self._generate_fallback_goal_tasks(goal_title, goal_description)
        
        try:
            logger.info(f"🤖 OPENAI SERVICE: Generating tasks for goal: {goal_title}")
            
            prompt = f"""
You are a productivity coach. Generate 5-7 actionable, specific tasks for this goal:

Goal Title: {goal_title}
Goal Description: {goal_description or "No additional description provided"}

Generate tasks that are:
1. Specific and actionable
2. Appropriately sized (30-90 minutes each)
3. Logically sequenced toward the goal
4. Varied in approach and skill requirements
5. Include realistic time estimates

Return your response as JSON with this exact structure:
{{
    "tasks": [
        {{
            "title": "Task title",
            "description": "Detailed description", 
            "priority": "high|medium|low",
            "estimatedDuration": 60
        }}
    ],
    "goalAnalysis": "Brief analysis of the goal and task strategy"
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful productivity coach. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ OPENAI SERVICE: Successfully generated {len(result.get('tasks', []))} tasks from goal description")
            
            return {
                "tasks": result.get("tasks", []),
                "goalAnalysis": result.get("goalAnalysis", "This goal requires focused effort and consistent action.")
            }
            
        except Exception as e:
            logger.error(f"❌ OPENAI SERVICE: Goal task generation failed, using fallback: {e}")
            return self._generate_fallback_goal_tasks(goal_title, goal_description)
    
    def _generate_fallback_goal_tasks(self, goal_title: str, goal_description: str) -> dict:
        """Generate fallback goal tasks when OpenAI is not available"""
        return {
            "tasks": [
                {
                    "title": f"Plan your approach to {goal_title}",
                    "description": "Break down this goal into smaller, manageable steps",
                    "priority": "high",
                    "estimatedDuration": 45
                },
                {
                    "title": f"Research strategies for {goal_title}",
                    "description": "Look up best practices and methods to achieve this goal",
                    "priority": "medium", 
                    "estimatedDuration": 60
                },
                {
                    "title": f"Take first action toward {goal_title}",
                    "description": goal_description or "Start with the most obvious first step",
                    "priority": "high",
                    "estimatedDuration": 30
                }
            ],
            "goalAnalysis": "This goal requires focused effort and consistent action. Break it down into smaller steps and track your progress regularly. (Note: This is a fallback response - OpenAI API not configured)"
        }
    
    async def generate_daily_breakdown(
        self, 
        tasks: List[dict], 
        goal_title: str, 
        goal_description: str = None,
        timeframe: str = "7 days"
    ) -> dict:
        """Generate daily breakdown for tasks"""
        
        if not self.is_configured:
            logger.warning("🤖 OPENAI SERVICE: Using fallback daily plan - OpenAI not configured")
            return self._generate_fallback_daily_plan(goal_title)
        
        try:
            logger.info(f"🤖 OPENAI SERVICE: Generating daily breakdown for: {goal_title}")
            
            task_titles = [task.get('title', 'Unknown task') for task in tasks]
            task_descriptions = [task.get('description', '') for task in tasks]
            
            prompt = f"""
You are a productivity coach. Create a daily breakdown plan for these tasks over {timeframe}:

Goal: {goal_title}
Description: {goal_description or "No additional description"}

Tasks to schedule:
{chr(10).join([f"- {title}: {desc}" for title, desc in zip(task_titles, task_descriptions)])}

Create a realistic daily schedule that:
1. Distributes tasks across {timeframe}
2. Considers task difficulty and time requirements
3. Allows for rest and flexibility
4. Builds momentum and maintains motivation

Return your response as JSON with this exact structure:
{{
    "weeklyPlan": [
        {{
            "day": "Monday",
            "tasks": [
                {{
                    "title": "Task name",
                    "description": "What to do",
                    "estimatedDuration": 60,
                    "priority": "high|medium|low"
                }}
            ]
        }}
    ],
    "totalDuration": 420,
    "tips": ["Tip 1", "Tip 2", "Tip 3"]
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful productivity coach. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ OPENAI SERVICE: Successfully generated daily breakdown")
            
            return {
                "weeklyPlan": result.get("weeklyPlan", []),
                "totalDuration": result.get("totalDuration", 420),
                "tips": result.get("tips", [])
            }
            
        except Exception as e:
            logger.error(f"❌ OPENAI SERVICE: Daily breakdown generation failed, using fallback: {e}")
            return self._generate_fallback_daily_plan(goal_title)
    
    def _generate_fallback_daily_plan(self, goal_title: str) -> dict:
        """Generate fallback daily plan when OpenAI is not available"""
        return {
            "weeklyPlan": [
                {
                    "day": "Monday",
                    "tasks": [
                        {
                            "title": "Start your goal journey",
                            "description": f"Begin working on {goal_title}",
                            "estimatedDuration": 60,
                            "priority": "high"
                        }
                    ]
                },
                {
                    "day": "Tuesday", 
                    "tasks": [
                        {
                            "title": "Continue progress",
                            "description": "Build on yesterday's momentum",
                            "estimatedDuration": 60,
                            "priority": "medium"
                        }
                    ]
                },
                {
                    "day": "Wednesday",
                    "tasks": [
                        {
                            "title": "Mid-week check-in",
                            "description": "Review progress and adjust if needed",
                            "estimatedDuration": 30,
                            "priority": "medium"
                        }
                    ]
                }
            ],
            "totalDuration": 150,
            "tips": [
                "Start small and build momentum",
                "Track your progress daily", 
                "Celebrate small wins",
                "Stay consistent even when motivation is low",
                "(Note: This is a fallback response - OpenAI API not configured)"
            ]
        }
    
    async def summarize_journal(self, journal: Journal) -> JournalSummaryResponse:
        """Generate AI summary and analysis of journal entry"""
        
        if not self.is_configured:
            logger.warning("🤖 OPENAI SERVICE: Using fallback journal analysis - OpenAI not configured")
            return self._generate_fallback_journal_summary()
        
        try:
            logger.info(f"🤖 OPENAI SERVICE: Analyzing journal entry")
            
            prompt = f"""
Analyze this journal entry and provide insights:

Title: {journal.title or "Untitled"}
Content: {journal.content}
Mood Level: {journal.mood_level.value if journal.mood_level else "Not specified"} (1=Very Sad, 5=Very Happy)
Date: {journal.created_at.strftime('%Y-%m-%d')}

Provide:
1. A concise summary (2-3 sentences)
2. Key themes identified
3. Sentiment score (-1 to 1, where -1 is very negative, 1 is very positive)
4. Mood analysis and insights

Return as JSON:
{{
    "summary": "Brief summary of the entry",
    "key_themes": ["theme1", "theme2", "theme3"],
    "sentiment_score": 0.5,
    "mood_analysis": "Detailed mood and emotional analysis"
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an empathetic AI therapist and journal analyst. Provide thoughtful, non-judgmental insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ OPENAI SERVICE: Successfully analyzed journal entry")
            
            return JournalSummaryResponse(
                summary=result["summary"],
                key_themes=result["key_themes"],
                sentiment_score=result["sentiment_score"],
                mood_analysis=result["mood_analysis"]
            )
            
        except Exception as e:
            logger.error(f"❌ OPENAI SERVICE: Journal analysis failed, using fallback: {e}")
            return self._generate_fallback_journal_summary()
    
    def _generate_fallback_journal_summary(self) -> JournalSummaryResponse:
        """Generate fallback journal summary when OpenAI is not available"""
        return JournalSummaryResponse(
            summary="Journal entry recorded successfully. (AI analysis not available - OpenAI API not configured)",
            key_themes=["reflection", "personal growth"],
            sentiment_score=0.0,
            mood_analysis="AI mood analysis is currently unavailable. Please check back later."
        )
    
    async def analyze_mood_patterns(
        self, 
        journals: List[Journal], 
        date_range_days: int = 7
    ) -> MoodAnalysisResponse:
        """Analyze mood patterns across multiple journal entries"""
        
        if not self.is_configured:
            logger.warning("🤖 OPENAI SERVICE: Using fallback mood analysis - OpenAI not configured")
            return self._generate_fallback_mood_analysis(len(journals))
        
        try:
            if not journals:
                return MoodAnalysisResponse(
                    overall_sentiment=0.0,
                    mood_trend="neutral",
                    insights=["No journal entries found for analysis"],
                    recommendations=["Start journaling regularly to track mood patterns"]
                )
            
            logger.info(f"🤖 OPENAI SERVICE: Analyzing mood patterns across {len(journals)} entries")
            
            # Prepare journal data for analysis
            journal_summaries = []
            for journal in journals[-10:]:  # Limit to last 10 entries
                summary = f"Date: {journal.created_at.strftime('%Y-%m-%d')}, "
                summary += f"Mood: {journal.mood_level.value if journal.mood_level else 'N/A'}, "
                summary += f"Content: {journal.content[:200]}..."
                journal_summaries.append(summary)
            
            prompt = f"""
Analyze these journal entries from the past {date_range_days} days for mood patterns and trends:

{chr(10).join(journal_summaries)}

Provide analysis including:
1. Overall sentiment score (-1 to 1)
2. Mood trend (improving/declining/stable/fluctuating)
3. Key insights about patterns, triggers, or themes
4. Practical recommendations for mood improvement

Return as JSON:
{{
    "overall_sentiment": 0.2,
    "mood_trend": "improving",
    "insights": ["insight1", "insight2", "insight3"],
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"]
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a skilled mood analyst and wellness coach. Provide actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"✅ OPENAI SERVICE: Successfully analyzed mood patterns")
            
            return MoodAnalysisResponse(
                overall_sentiment=result["overall_sentiment"],
                mood_trend=result["mood_trend"],
                insights=result["insights"],
                recommendations=result["recommendations"]
            )
            
        except Exception as e:
            logger.error(f"❌ OPENAI SERVICE: Mood analysis failed, using fallback: {e}")
            return self._generate_fallback_mood_analysis(len(journals))
    
    def _generate_fallback_mood_analysis(self, journal_count: int) -> MoodAnalysisResponse:
        """Generate fallback mood analysis when OpenAI is not available"""
        return MoodAnalysisResponse(
            overall_sentiment=0.0,
            mood_trend="stable",
            insights=[
                f"Analysis based on {journal_count} journal entries",
                "AI mood analysis currently unavailable",
                "Continue journaling for better insights"
            ],
            recommendations=[
                "Continue journaling regularly",
                "Focus on mindfulness and self-reflection",
                "Check back later for AI-powered insights"
            ]
        )

# Singleton instance
openai_service = OpenAIService() 