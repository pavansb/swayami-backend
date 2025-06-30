from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models import Goal, GoalCreate, GoalUpdate, GoalStatus
from app.repositories.goal_repository import goal_repository
from app.repositories.task_repository import task_repository
from app.auth import get_current_user_id

router = APIRouter(prefix="/goals", tags=["goals"])

@router.post("/", response_model=Goal)
async def create_goal(
    goal_data: GoalCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new goal"""
    try:
        goal = await goal_repository.create_goal(user_id, goal_data)
        return goal
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating goal: {str(e)}")

@router.get("/", response_model=List[Goal])
async def get_goals(
    status: Optional[GoalStatus] = Query(None, description="Filter by goal status"),
    skip: int = Query(0, ge=0, description="Number of goals to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of goals to return"),
    user_id: str = Depends(get_current_user_id)
):
    """Get goals for the current user"""
    try:
        goals = await goal_repository.get_goals_by_user(
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit
        )
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching goals: {str(e)}")

@router.get("/{goal_id}", response_model=Goal)
async def get_goal(
    goal_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific goal by ID"""
    goal = await goal_repository.get_goal_by_id(goal_id, user_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal

@router.put("/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: str,
    goal_update: GoalUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update a goal"""
    goal = await goal_repository.update_goal(goal_id, user_id, goal_update)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal

@router.patch("/{goal_id}/progress")
async def update_goal_progress(
    goal_id: str,
    progress: float = Query(..., ge=0, le=100, description="Progress percentage (0-100)"),
    user_id: str = Depends(get_current_user_id)
):
    """Update goal progress percentage"""
    goal = await goal_repository.update_goal_progress(goal_id, user_id, progress)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Progress updated successfully", "goal": goal}

@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a goal"""
    success = await goal_repository.delete_goal(goal_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal deleted successfully"}

@router.get("/{goal_id}/tasks")
async def get_goal_tasks(
    goal_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get all tasks for a specific goal"""
    # First verify the goal exists and belongs to the user
    goal = await goal_repository.get_goal_by_id(goal_id, user_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    tasks = await task_repository.get_tasks_by_goal(goal_id, user_id)
    return {
        "goal": goal,
        "tasks": tasks,
        "task_count": len(tasks)
    }

@router.get("/category/{category}")
async def get_goals_by_category(
    category: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get goals by category"""
    try:
        goals = await goal_repository.get_goals_by_category(user_id, category)
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching goals by category: {str(e)}") 