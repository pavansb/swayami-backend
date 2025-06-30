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
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    async def generate_tasks_for_goal(
        self, 
        goal: Goal, 
        request: TaskGenerationRequest,
        existing_tasks: List[Task] = None
    ) -> TaskGenerationResponse:
        """Generate AI-powered tasks for a specific goal"""
        try:
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
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful productivity coach. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            
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
            logger.error(f"Error generating tasks: {e}")
            # Return fallback tasks
            fallback_tasks = [
                TaskCreate(
                    title=f"Work on: {goal.title}",
                    description="Break down this goal into smaller steps",
                    priority=goal.priority,
                    estimated_duration=60,
                    tags=["planning"],
                    goal_id=goal.id
                )
            ]
            return TaskGenerationResponse(
                tasks=fallback_tasks,
                reasoning="Generated fallback task due to AI service error"
            )
    
    async def summarize_journal(self, journal: Journal) -> JournalSummaryResponse:
        """Generate AI summary and analysis of journal entry"""
        try:
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
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an empathetic AI therapist and journal analyst. Provide thoughtful, non-judgmental insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return JournalSummaryResponse(
                summary=result["summary"],
                key_themes=result["key_themes"],
                sentiment_score=result["sentiment_score"],
                mood_analysis=result["mood_analysis"]
            )
            
        except Exception as e:
            logger.error(f"Error summarizing journal: {e}")
            return JournalSummaryResponse(
                summary="Unable to generate summary at this time.",
                key_themes=["reflection"],
                sentiment_score=0.0,
                mood_analysis="Analysis unavailable due to service error."
            )
    
    async def analyze_mood_patterns(
        self, 
        journals: List[Journal], 
        date_range_days: int = 7
    ) -> MoodAnalysisResponse:
        """Analyze mood patterns across multiple journal entries"""
        try:
            if not journals:
                return MoodAnalysisResponse(
                    overall_sentiment=0.0,
                    mood_trend="neutral",
                    insights=["No journal entries found for analysis"],
                    recommendations=["Start journaling regularly to track mood patterns"]
                )
            
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
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a skilled mood analyst and wellness coach. Provide actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return MoodAnalysisResponse(
                overall_sentiment=result["overall_sentiment"],
                mood_trend=result["mood_trend"],
                insights=result["insights"],
                recommendations=result["recommendations"]
            )
            
        except Exception as e:
            logger.error(f"Error analyzing mood patterns: {e}")
            return MoodAnalysisResponse(
                overall_sentiment=0.0,
                mood_trend="stable",
                insights=["Unable to analyze mood patterns at this time"],
                recommendations=["Continue journaling regularly for better insights"]
            )

# Singleton instance
openai_service = OpenAIService() 