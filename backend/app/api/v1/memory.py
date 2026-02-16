from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter()


@router.get("/profile")
async def get_user_profile(db: Session = Depends(get_db)):
    """Get user profile (long-term memory)."""
    from app.memory.long_term import LongTermMemory
    ltm = LongTermMemory()
    profile = await ltm.retrieve("demo_user_123", db)
    return {"profile": profile}


@router.put("/profile")
async def update_user_profile(db: Session = Depends(get_db)):
    """Update user profile."""
    # TODO: Implement profile update
    return {"status": "updated"}


@router.post("/feedback")
async def submit_feedback(db: Session = Depends(get_db)):
    """Submit feedback correction."""
    # TODO: Implement feedback submission
    return {"status": "submitted"}


@router.delete("/clear")
async def clear_memory(db: Session = Depends(get_db)):
    """Clear all memory for current user."""
    # TODO: Implement memory clearing
    return {"status": "cleared"}
