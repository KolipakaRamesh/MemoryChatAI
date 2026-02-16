from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.memory.base import BaseMemory
from app.models.database import FeedbackCorrection
from app.observability.logger import get_logger

logger = get_logger(__name__)


class FeedbackMemory(BaseMemory):
    """Feedback memory implementation for learning from corrections."""
    
    async def retrieve(
        self, 
        user_id: str,
        db: Session,
        current_context: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Retrieve relevant feedback corrections.
        
        Args:
            user_id: User identifier
            db: Database session
            current_context: Current query context for relevance ranking
            limit: Maximum number of corrections to retrieve
            
        Returns:
            Dictionary with corrections and relevance scores
        """
        logger.info(f"Retrieving feedback memory for user: {user_id}")
        
        # Query recent corrections
        corrections = db.query(FeedbackCorrection)\
            .filter(FeedbackCorrection.user_id == user_id)\
            .order_by(FeedbackCorrection.created_at.desc())\
            .limit(limit * 2)\
            .all()  # Get more than needed for filtering
        
        if not corrections:
            logger.info(f"No feedback corrections found for user: {user_id}")
            return {"corrections": []}
        
        # Format corrections
        correction_dicts = []
        for correction in corrections[:limit]:
            correction_dicts.append({
                "id": correction.feedback_id,
                "correction_type": correction.correction_type,
                "user_correction": correction.user_correction,
                "corrected_response": correction.corrected_response,
                "application_count": correction.applied_count,
                "relevance_score": 1.0,  # Default relevance (can be enhanced with embeddings)
                "timestamp": correction.created_at.isoformat()
            })
        
        logger.info(f"Retrieved {len(correction_dicts)} feedback corrections")
        
        return {"corrections": correction_dicts}
    
    async def store(
        self,
        feedback_id: str,
        user_id: str,
        conversation_id: str,
        message_id: str,
        correction_type: str,
        user_correction: str,
        corrected_response: Optional[str],
        context_snapshot: Dict[str, Any],
        db: Session
    ) -> None:
        """
        Store a new feedback correction.
        
        Args:
            feedback_id: Unique feedback identifier
            user_id: User identifier
            conversation_id: Conversation identifier
            message_id: Message that was corrected
            correction_type: Type of correction
            user_correction: User's correction text
            corrected_response: Corrected response (optional)
            context_snapshot: Memory state at time of error
            db: Database session
        """
        logger.info(f"Storing feedback correction: {feedback_id}")
        
        try:
            correction = FeedbackCorrection(
                feedback_id=feedback_id,
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=message_id,
                correction_type=correction_type,
                user_correction=user_correction,
                corrected_response=corrected_response,
                context_snapshot=context_snapshot,
                applied_count=0
            )
            
            db.add(correction)
            db.commit()
            
            logger.info(f"Stored feedback correction: {feedback_id}")
            
        except Exception as e:
            logger.error(f"Error storing feedback correction: {e}")
            db.rollback()
    
    async def clear(self, user_id: str, db: Session) -> None:
        """
        Clear all feedback corrections for a user.
        
        Args:
            user_id: User identifier
            db: Database session
        """
        try:
            db.query(FeedbackCorrection)\
                .filter(FeedbackCorrection.user_id == user_id)\
                .delete()
            db.commit()
            
            logger.info(f"Cleared feedback memory for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing feedback memory: {e}")
            db.rollback()
    
    async def increment_application_count(
        self,
        feedback_id: str,
        db: Session
    ) -> None:
        """
        Increment the application count for a correction.
        
        Args:
            feedback_id: Feedback identifier
            db: Database session
        """
        try:
            correction = db.query(FeedbackCorrection)\
                .filter(FeedbackCorrection.feedback_id == feedback_id)\
                .first()
            
            if correction:
                correction.applied_count += 1
                db.commit()
                logger.info(f"Incremented application count for: {feedback_id}")
                
        except Exception as e:
            logger.error(f"Error incrementing application count: {e}")
            db.rollback()
