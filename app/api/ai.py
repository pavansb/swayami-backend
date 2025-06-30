from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from app.models import (
    TaskGenerationRequest, TaskGenerationResponse, Task,
    JournalSummaryRequest, JournalSummaryResponse,
    MoodAnalysisRequest, MoodAnalysisResponse
)
from app.repositories.goal_repository import goal_repository
from app.repositories.task_repository import task_repository
from app.repositories.journal_repository import journal_repository
from app.services.openai_service import openai_service
from app.auth import get_current_user_id

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/generate-tasks", response_model=TaskGenerationResponse)
async def generate_tasks(
    request: TaskGenerationRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """Generate AI-powered tasks for a specific goal"""
    try:
        # Get the goal and verify it belongs to the user
        goal = await goal_repository.get_goal_by_id(request.goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        # Get existing tasks for context
        existing_tasks = await task_repository.get_tasks_by_goal(request.goal_id, user_id)
        
        # Generate tasks using AI
        response = await openai_service.generate_tasks_for_goal(
            goal=goal,
            request=request,
            existing_tasks=existing_tasks
        )
        
        # Save generated tasks in background
        async def save_generated_tasks():
            for task_data in response.tasks:
                try:
                    await task_repository.create_ai_task(user_id, task_data)
                except Exception as e:
                    print(f"Error saving AI task: {e}")
        
        background_tasks.add_task(save_generated_tasks)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating tasks: {str(e)}")

@router.post("/summarize-journal", response_model=JournalSummaryResponse)
async def summarize_journal(
    request: JournalSummaryRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """Generate AI summary and analysis of a journal entry"""
    try:
        # Get the journal and verify it belongs to the user
        journal = await journal_repository.get_journal_by_id(request.journal_id, user_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found")
        
        # Generate summary using AI
        response = await openai_service.summarize_journal(journal)
        
        # Update journal with AI analysis in background
        async def update_journal_analysis():
            try:
                await journal_repository.update_ai_analysis(
                    journal_id=request.journal_id,
                    user_id=user_id,
                    ai_summary=response.summary,
                    sentiment_score=response.sentiment_score
                )
            except Exception as e:
                print(f"Error updating journal analysis: {e}")
        
        background_tasks.add_task(update_journal_analysis)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing journal: {str(e)}")

@router.post("/analyze-mood", response_model=MoodAnalysisResponse)
async def analyze_mood(
    request: MoodAnalysisRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Analyze mood patterns across multiple journal entries"""
    try:
        # Get the journals and verify they belong to the user
        journals = []
        for journal_id in request.journal_ids:
            journal = await journal_repository.get_journal_by_id(journal_id, user_id)
            if journal:
                journals.append(journal)
        
        if not journals:
            raise HTTPException(status_code=404, detail="No valid journals found")
        
        # Analyze mood patterns using AI
        response = await openai_service.analyze_mood_patterns(
            journals=journals,
            date_range_days=request.date_range_days
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing mood: {str(e)}")

@router.get("/analyze-mood/recent")
async def analyze_recent_mood(
    days: int = 7,
    user_id: str = Depends(get_current_user_id)
):
    """Analyze mood patterns from recent journal entries"""
    try:
        # Get recent journals
        journals = await journal_repository.get_journals_by_user(
            user_id=user_id,
            days_back=days,
            limit=50
        )
        
        if not journals:
            return {
                "message": "No journal entries found for mood analysis",
                "days_analyzed": days,
                "journals_count": 0
            }
        
        # Analyze mood patterns using AI
        response = await openai_service.analyze_mood_patterns(
            journals=journals,
            date_range_days=days
        )
        
        return {
            "analysis": response,
            "days_analyzed": days,
            "journals_count": len(journals),
            "date_range": {
                "start": journals[-1].created_at if journals else None,
                "end": journals[0].created_at if journals else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing recent mood: {str(e)}")

@router.get("/quick-recommendations")
async def get_quick_recommendations(
    user_id: str = Depends(get_current_user_id)
):
    """Get quick AI-powered recommendations based on recent activity"""
    try:
        # Get recent data
        pending_tasks = await task_repository.get_pending_tasks(user_id, limit=5)
        recent_journals = await journal_repository.get_recent_journals(user_id, limit=3)
        active_goals = await goal_repository.get_goals_by_user(user_id, limit=5)
        
        recommendations = []
        
        # Task-based recommendations
        if pending_tasks:
            high_priority_tasks = [t for t in pending_tasks if t.priority.value == "high"]
            if high_priority_tasks:
                recommendations.append({
                    "type": "task_priority",
                    "message": f"You have {len(high_priority_tasks)} high-priority tasks pending. Consider tackling them first.",
                    "action": "focus_on_priority_tasks"
                })
        
        # Journal-based recommendations
        if recent_journals:
            avg_mood = sum([j.mood_score for j in recent_journals if j.mood_score]) / len([j for j in recent_journals if j.mood_score]) if any(j.mood_score for j in recent_journals) else None
            if avg_mood and avg_mood < 3:
                recommendations.append({
                    "type": "mood_support",
                    "message": "Your recent journal entries suggest you might benefit from some self-care activities.",
                    "action": "suggest_wellness_activities"
                })
        
        # Goal-based recommendations
        if active_goals:
            goals_without_tasks = []
            for goal in active_goals:
                goal_tasks = await task_repository.get_tasks_by_goal(goal.id, user_id)
                if not goal_tasks:
                    goals_without_tasks.append(goal)
            
            if goals_without_tasks:
                recommendations.append({
                    "type": "goal_planning",
                    "message": f"You have {len(goals_without_tasks)} goals without specific tasks. Break them down into actionable steps.",
                    "action": "create_goal_tasks"
                })
        
        return {
            "recommendations": recommendations,
            "stats": {
                "pending_tasks": len(pending_tasks),
                "recent_journals": len(recent_journals),
                "active_goals": len(active_goals)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}") 