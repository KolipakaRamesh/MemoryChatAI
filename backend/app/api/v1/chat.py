from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.models.database import User
from app.core.orchestrator import chat_orchestrator
from app.observability.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=ChatMessageResponse)
async def chat(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Process chat message and return response with observability data.
    
    Args:
        request: Chat message request
        db: Database session
        
    Returns:
        Chat response with memory dashboard data
    """
    try:
        # Development placeholder for user identification
        user_id = "demo_user_123"
        
        # Ensure demo user exists (FK constraint requires a User row)
        if not db.query(User).filter(User.user_id == user_id).first():
            demo_user = User(
                user_id=user_id,
                email="demo@example.com",
                hashed_password="N/A",
                full_name="Demo User"
            )
            db.add(demo_user)
            db.commit()
            logger.info(f"Auto-created demo user: {user_id}")
        
        logger.info(f"Received chat request from user: {user_id}")
        
        result = await chat_orchestrator.process_message(
            user_id=user_id,
            user_message=request.message,
            conversation_id=request.conversation_id,
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations(
    db: Session = Depends(get_db)
):
    """List all conversations for the current user."""
    # TODO: Implement conversation listing
    return {"conversations": []}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get specific conversation with all messages."""
    # TODO: Implement conversation retrieval
    return {"conversation_id": conversation_id, "messages": []}
