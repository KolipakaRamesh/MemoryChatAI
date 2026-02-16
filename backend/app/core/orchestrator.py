import uuid
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.memory.manager import MemoryManager
from app.core.prompt_builder import prompt_builder
from app.core.token_manager import token_manager
from app.services.llm_service import llm_service
from app.models.database import Conversation, RequestTrace
from app.observability.logger import get_logger
import time

logger = get_logger(__name__)


class ChatOrchestrator:
    """Main orchestrator for chat processing."""
    
    def __init__(self):
        self.memory_manager = MemoryManager()
    
    async def process_message(
        self,
        user_id: str,
        user_message: str,
        conversation_id: str = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Process user message through complete pipeline.
        
        Args:
            user_id: User identifier
            user_message: User's message
            conversation_id: Conversation ID (creates new if None)
            db: Database session
            
        Returns:
            Response with observability data
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        logger.info(f"Processing message for user: {user_id}, request: {request_id}")
        
        try:
            # Create or get conversation
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                conversation = Conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    title=user_message[:100]  # Use first 100 chars as title
                )
                db.add(conversation)
                db.commit()
                logger.info(f"Created new conversation: {conversation_id}")
            
            # Step 1: Generate embedding for user message
            query_embedding = await llm_service.generate_embedding(user_message)
            
            # Step 2: Retrieve all memories in parallel
            retrieval_start = time.time()
            memory_snapshot = await self.memory_manager.retrieve_all_memories(
                user_id=user_id,
                conversation_id=conversation_id,
                query=user_message,
                query_embedding=query_embedding,
                db=db
            )
            retrieval_latency = (time.time() - retrieval_start) * 1000

            # Step 2.5: Detect manual feedback trigger
            feedback_added = False
            if user_message.lower().strip().startswith("incorrect:"):
                try:
                    feedback_id = str(uuid.uuid4())
                    await self.memory_manager.feedback.store(
                        feedback_id=feedback_id,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        message_id=request_id,
                        correction_type="manual_user_correction",
                        user_correction=user_message,
                        corrected_response=None,
                        context_snapshot={
                            "short_term": len(memory_snapshot["short_term_memory"]["messages"]),
                            "has_long_term": bool(memory_snapshot["long_term_memory"])
                        },
                        db=db
                    )
                    logger.info(f"Captured manual feedback: {feedback_id}")
                    feedback_added = True
                    # Refresh feedback memory snapshot immediately
                    memory_snapshot["feedback_memory"] = await self.memory_manager.feedback.retrieve(
                        user_id=user_id, db=db, current_context=user_message
                    )
                except Exception as fe:
                    logger.error(f"Failed to capture manual feedback: {fe}")

            # Step 3: Build optimized prompt
            prompt_start = time.time()
            final_prompt, token_breakdown = prompt_builder.build_prompt(
                memory_snapshot=memory_snapshot,
                user_message=user_message
            )
            prompt_latency = (time.time() - prompt_start) * 1000
            
            # Step 4: Generate response from LLM
            llm_start = time.time()
            llm_response = await llm_service.generate(
                prompt=final_prompt,
                max_tokens=1000,
                temperature=0.7
            )
            assistant_response = llm_response["response"]
            llm_latency = (time.time() - llm_start) * 1000
            
            # Step 5-8: Storage operations
            storage_start = time.time()
            # Step 5: Store user message
            user_message_id = str(uuid.uuid4())
            user_embedding = query_embedding
            
            await self.memory_manager.store_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=user_message_id,
                content=user_message,
                role="user",
                embedding=user_embedding,
                metadata={
                    "tokens": token_manager.count_tokens(user_message),
                    "conversation_title": user_message[:100]
                },
                db=db
            )
            
            # Step 6: Store assistant response
            assistant_message_id = str(uuid.uuid4())
            assistant_embedding = await llm_service.generate_embedding(assistant_response)
            
            await self.memory_manager.store_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                content=assistant_response,
                role="assistant",
                embedding=assistant_embedding,
                metadata={
                    "tokens": llm_response["completion_tokens"],
                    "conversation_title": user_message[:100]
                },
                db=db
            )
            
            # Step 7: Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost = token_manager.calculate_cost(
                llm_response["prompt_tokens"],
                llm_response["completion_tokens"],
                llm_response["model"]
            )
            
            # Step 8: Store request trace
            trace = RequestTrace(
                request_id=request_id,
                user_id=user_id,
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_response=assistant_response,
                prompt_tokens=llm_response["prompt_tokens"],
                completion_tokens=llm_response["completion_tokens"],
                total_tokens=llm_response["total_tokens"],
                latency_ms=latency_ms,
                llm_provider=llm_response["provider"],
                model_name=llm_response["model"],
                memory_snapshot=memory_snapshot
            )
            db.add(trace)
            db.commit()
            storage_latency = (time.time() - storage_start) * 1000
            
            # Step 8.5: Final refresh of all memories for the observability snapshot
            memory_snapshot = await self.memory_manager.retrieve_all_memories(
                user_id=user_id,
                conversation_id=conversation_id,
                query=user_message,
                query_embedding=query_embedding,
                db=db
            )

            # Step 9: Build observability data
            observability_data = {
                "request_id": request_id,
                "short_term_memory": memory_snapshot["short_term_memory"],
                "long_term_memory": memory_snapshot["long_term_memory"],
                "semantic_memory": memory_snapshot["semantic_memory"],
                "feedback_memory": memory_snapshot["feedback_memory"],
                "token_usage": {
                    "breakdown": token_breakdown,
                    "total": llm_response["prompt_tokens"],
                    "estimated_response": llm_response["completion_tokens"],
                    "cost": cost
                },
                "request_trace": {
                    "steps": [
                        {"name": "Memory Retrieval", "latency_ms": retrieval_latency},
                        {"name": "Prompt Construction", "latency_ms": prompt_latency},
                        {"name": "LLM Call", "latency_ms": llm_latency},
                        {"name": "Storage / Trace", "latency_ms": storage_latency}
                    ],
                    "total_latency_ms": latency_ms
                }
            }
            
            logger.info(
                f"Completed request {request_id}: "
                f"{llm_response['total_tokens']} tokens, "
                f"${cost:.6f}, {latency_ms:.0f}ms"
            )
            
            return {
                "response": assistant_response,
                "conversation_id": conversation_id,
                "message_id": assistant_message_id,
                "observability": observability_data
            }
        
        except Exception as e:
            logger.error(f"Error in process_message pipeline: {e}", exc_info=True)
            db.rollback()
            raise


# Global orchestrator instance
chat_orchestrator = ChatOrchestrator()
