from collections import deque
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.memory.base import BaseMemory
from app.models.database import Message
from app.observability.logger import get_logger

logger = get_logger(__name__)


class ShortTermMemory(BaseMemory):
    """Short-term memory implementation using in-memory cache."""
    
    def __init__(self, max_messages: int = 20):
        self.cache: Dict[str, deque] = {}
        self.max_messages = max_messages
    
    async def retrieve(
        self, 
        conversation_id: str, 
        db: Session,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve recent messages from cache or database.
        
        Args:
            conversation_id: Conversation identifier
            db: Database session
            limit: Number of recent messages to retrieve
            
        Returns:
            Dictionary with messages and optional summary
        """
        logger.info(f"Retrieving short-term memory for conversation: {conversation_id}")
        
        # Check cache first
        if conversation_id in self.cache:
            message_dicts = list(self.cache[conversation_id])[-limit:]
            logger.info(f"Retrieved {len(message_dicts)} messages from cache")
        else:
            # Cache miss - load from database
            db_messages = db.query(Message)\
                .filter(Message.conversation_id == conversation_id)\
                .order_by(Message.created_at.desc())\
                .limit(limit)\
                .all()
            
            # Reverse to chronological order
            db_messages = list(reversed(db_messages))
            
            # Convert ORM objects to dicts immediately to avoid DetachedInstanceError
            message_dicts = [self._msg_to_dict(m) for m in db_messages]
            
            # Populate cache with plain dicts (not ORM objects)
            self.cache[conversation_id] = deque(message_dicts, maxlen=self.max_messages)
            logger.info(f"Retrieved {len(message_dicts)} messages from database and cached")
        
        return {
            "messages": message_dicts,
            "summary": None  # Will be populated if summarization occurred
        }
    
    @staticmethod
    def _msg_to_dict(msg) -> Dict[str, Any]:
        """Convert a Message ORM object to a plain dict for safe caching."""
        return {
            "id": msg.message_id if hasattr(msg, 'message_id') else str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "tokens": msg.tokens_used if hasattr(msg, 'tokens_used') else 0,
            "timestamp": msg.created_at.isoformat() if hasattr(msg, 'created_at') and hasattr(msg.created_at, 'isoformat') else str(getattr(msg, 'created_at', '')),
            "includedInPrompt": True
        }

    async def store(
        self, 
        conversation_id: str, 
        message: Message
    ) -> None:
        """
        Store message in cache.
        
        Args:
            conversation_id: Conversation identifier
            message: Message object to store
        """
        if conversation_id not in self.cache:
            self.cache[conversation_id] = deque(maxlen=self.max_messages)
        
        self.cache[conversation_id].append(self._msg_to_dict(message))
        logger.info(f"Stored message in cache for conversation: {conversation_id}")
    
    async def clear(self, conversation_id: str) -> None:
        """
        Clear cache for a conversation.
        
        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.cache:
            del self.cache[conversation_id]
            logger.info(f"Cleared cache for conversation: {conversation_id}")
    
    def should_summarize(
        self, 
        conversation_id: str, 
        token_threshold: int = 2000
    ) -> bool:
        """
        Check if conversation should be summarized.
        
        Args:
            conversation_id: Conversation identifier
            token_threshold: Token limit before summarization
            
        Returns:
            True if summarization is needed
        """
        if conversation_id not in self.cache:
            return False
        
        messages = self.cache[conversation_id]
        total_tokens = sum(
            msg.tokens_used if hasattr(msg, 'tokens_used') else 0 
            for msg in messages
        )
        
        should_summarize = total_tokens > token_threshold
        
        if should_summarize:
            logger.info(
                f"Summarization needed for {conversation_id}: "
                f"{total_tokens} tokens exceeds threshold {token_threshold}"
            )
        
        return should_summarize
