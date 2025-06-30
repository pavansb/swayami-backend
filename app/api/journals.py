from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from app.models import Journal, JournalCreate, JournalUpdate
from app.repositories.journal_repository import journal_repository
from app.auth import get_current_user_id

router = APIRouter(prefix="/journals", tags=["journals"])

@router.post("/", response_model=Journal)
async def create_journal(
    journal_data: JournalCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new journal entry"""
    try:
        journal = await journal_repository.create_journal(user_id, journal_data)
        return journal
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating journal: {str(e)}")

@router.get("/", response_model=List[Journal])
async def get_journals(
    days_back: Optional[int] = Query(None, ge=1, le=365, description="Filter entries from last N days"),
    skip: int = Query(0, ge=0, description="Number of journals to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of journals to return"),
    user_id: str = Depends(get_current_user_id)
):
    """Get journal entries for the current user"""
    try:
        journals = await journal_repository.get_journals_by_user(
            user_id=user_id,
            days_back=days_back,
            skip=skip,
            limit=limit
        )
        return journals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching journals: {str(e)}")

@router.get("/recent", response_model=List[Journal])
async def get_recent_journals(
    limit: int = Query(10, ge=1, le=50, description="Number of recent journals to return"),
    user_id: str = Depends(get_current_user_id)
):
    """Get recent journal entries"""
    try:
        journals = await journal_repository.get_recent_journals(user_id, limit)
        return journals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent journals: {str(e)}")

@router.get("/search")
async def search_journals(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=50, description="Number of results to return"),
    user_id: str = Depends(get_current_user_id)
):
    """Search journal entries by content"""
    try:
        journals = await journal_repository.search_journals(user_id, q, limit)
        return {
            "query": q,
            "results": journals,
            "count": len(journals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching journals: {str(e)}")

@router.get("/{journal_id}", response_model=Journal)
async def get_journal(
    journal_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific journal entry by ID"""
    journal = await journal_repository.get_journal_by_id(journal_id, user_id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal

@router.put("/{journal_id}", response_model=Journal)
async def update_journal(
    journal_id: str,
    journal_update: JournalUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update a journal entry"""
    journal = await journal_repository.update_journal(journal_id, user_id, journal_update)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal

@router.delete("/{journal_id}")
async def delete_journal(
    journal_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a journal entry"""
    success = await journal_repository.delete_journal(journal_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Journal not found")
    return {"message": "Journal deleted successfully"}

@router.get("/date-range/entries")
async def get_journals_by_date_range(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    user_id: str = Depends(get_current_user_id)
):
    """Get journal entries within a specific date range"""
    try:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        journals = await journal_repository.get_journals_by_date_range(
            user_id, start_date, end_date
        )
        return {
            "start_date": start_date,
            "end_date": end_date,
            "journals": journals,
            "count": len(journals)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching journals by date range: {str(e)}") 