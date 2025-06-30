from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models import Task, TaskCreate, TaskUpdate, TaskStatus
from app.repositories.task_repository import task_repository
from app.repositories.goal_repository import goal_repository
from app.auth import get_current_user_id

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=Task)
async def create_task(
    task_data: TaskCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new task"""
    try:
        # If goal_id is provided, verify it exists and belongs to the user
        if task_data.goal_id:
            goal = await goal_repository.get_goal_by_id(task_data.goal_id, user_id)
            if not goal:
                raise HTTPException(status_code=404, detail="Goal not found")
        
        task = await task_repository.create_task(user_id, task_data)
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@router.get("/", response_model=List[Task])
async def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    goal_id: Optional[str] = Query(None, description="Filter by goal ID"),
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of tasks to return"),
    user_id: str = Depends(get_current_user_id)
):
    """Get tasks for the current user"""
    try:
        tasks = await task_repository.get_tasks_by_user(
            user_id=user_id,
            status=status,
            goal_id=goal_id,
            skip=skip,
            limit=limit
        )
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

@router.get("/pending", response_model=List[Task])
async def get_pending_tasks(
    limit: int = Query(10, ge=1, le=50, description="Number of pending tasks to return"),
    user_id: str = Depends(get_current_user_id)
):
    """Get pending tasks for today's recommendations"""
    try:
        tasks = await task_repository.get_pending_tasks(user_id, limit)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pending tasks: {str(e)}")

@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific task by ID"""
    task = await task_repository.get_task_by_id(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update a task"""
    # If goal_id is being updated, verify it exists and belongs to the user
    if task_update.goal_id:
        goal = await goal_repository.get_goal_by_id(task_update.goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
    
    task = await task_repository.update_task(task_id, user_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}/complete")
async def mark_task_completed(
    task_id: str,
    actual_duration: Optional[int] = Query(None, description="Actual time spent in minutes"),
    user_id: str = Depends(get_current_user_id)
):
    """Mark a task as completed"""
    task = await task_repository.mark_task_completed(task_id, user_id, actual_duration)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task marked as completed", "task": task}

@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: TaskStatus,
    user_id: str = Depends(get_current_user_id)
):
    """Update task status"""
    task_update = TaskUpdate(status=status)
    task = await task_repository.update_task(task_id, user_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task status updated", "task": task}

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a task"""
    success = await task_repository.delete_task(task_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"} 