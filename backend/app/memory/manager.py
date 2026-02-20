from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.memory.semantic import SemanticMemory
from app.memory.feedback import FeedbackMemory
from app.observability.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """Centralized memory manager coordinating all memory types."""
    
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.semantic = SemanticMemory()
        self.feedback = FeedbackMemory()
    
    async def retrieve_all_memories(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        query_embedding: List[float],
        db: Session
    ) -> Dict[str, Any]:
        """
        Retrieve all memory types in parallel.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            query: User's current query
            query_embedding: Embedding of the query
            db: Database session
            
        Returns:
            Aggregated memory snapshot
        """
        logger.info(f"Retrieving all memories for user: {user_id}, conversation: {conversation_id}")
        
        # Retrieve all memories (in production, use asyncio.gather for parallel execution)
        short_term_memory = await self.short_term.retrieve(conversation_id, db)
        long_term_memory = await self.long_term.retrieve(user_id, db)
        semantic_memory = await self.semantic.retrieve(user_id=user_id, query_embedding=query_embedding)
        feedback_memory = await self.feedback.retrieve(user_id, db, query)
        
        memory_snapshot = {
            "short_term_memory": short_term_memory,
            "long_term_memory": long_term_memory,
            "semantic_memory": semantic_memory,
            "feedback_memory": feedback_memory
        }
        
        logger.info("Successfully retrieved all memory types")
        
        return memory_snapshot
    
    async def store_message(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        content: str,
        role: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        db: Session
    ) -> None:
        """
        Store message in appropriate memory systems.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            message_id: Message identifier
            content: Message content
            role: Message role (user/assistant)
            embedding: Message embedding
            metadata: Additional metadata
            db: Database session
        """
        from app.models.database import Message
        
        # Create message object
        message = Message(
            message_id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=metadata.get("tokens", 0),
            embedding_id=message_id
        )
        
        # Store in database
        db.add(message)
        db.commit()
        
        # Store in short-term memory cache
        await self.short_term.store(conversation_id, message)
        
        # Store in semantic memory (ChromaDB)
        await self.semantic.store(
            message_id=message_id,
            user_id=user_id,
            content=content,
            embedding=embedding,
            metadata=metadata
        )
        
        logger.info(f"Stored message {message_id} in all memory systems")
