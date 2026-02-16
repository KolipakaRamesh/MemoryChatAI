from typing import Dict, Any
from app.core.token_manager import token_manager
from app.config import settings
from app.observability.logger import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """Prompt construction with layered architecture."""
    
    # Layer order and token allocation
    LAYER_ORDER = [
        "system_instructions",
        "user_profile",
        "feedback_corrections",
        "conversation_summary",
        "semantic_context",
        "recent_messages",
        "current_message"
    ]
    
    TOKEN_ALLOCATION = {
        "system_instructions": 300,
        "user_profile": 200,
        "feedback_corrections": 150,
        "conversation_summary": 250,
        "semantic_context": 400,
        "recent_messages": 800,
        "current_message": 200
    }
    
    def build_prompt(
        self,
        memory_snapshot: Dict[str, Any],
        user_message: str
    ) -> tuple[str, Dict[str, int]]:
        """
        Construct optimized prompt with token awareness.
        
        Args:
            memory_snapshot: Aggregated memory data
            user_message: Current user message
            
        Returns:
            Tuple of (Final prompt string, token_breakdown)
        """
        logger.info("Building prompt from memory snapshot")
        
        layers = {}
        
        # Layer 1: System Instructions
        layers["system_instructions"] = self._build_system_layer()
        
        # Layer 2: User Profile (Long-Term Memory)
        layers["user_profile"] = self._build_profile_layer(
            memory_snapshot.get("long_term_memory", {})
        )
        
        # Layer 3: Feedback Corrections
        layers["feedback_corrections"] = self._build_feedback_layer(
            memory_snapshot.get("feedback_memory", {})
        )
        
        # Layer 4: Conversation Summary
        layers["conversation_summary"] = self._build_summary_layer(
            memory_snapshot.get("short_term_memory", {}).get("summary")
        )
        
        # Layer 5: Semantic Context
        layers["semantic_context"] = self._build_semantic_layer(
            memory_snapshot.get("semantic_memory", {})
        )
        
        # Layer 6: Recent Messages (Short-Term Memory)
        layers["recent_messages"] = self._build_recent_messages_layer(
            memory_snapshot.get("short_term_memory", {})
        )
        
        # Layer 7: Current Message
        layers["current_message"] = f"\n\nUser: {user_message}\n\nAssistant:"
        
        # Optimize and assemble
        optimized_prompt, token_breakdown = self._optimize_layers(layers)
        
        token_count = sum(token_breakdown.values())
        logger.info(f"Built prompt with {token_count} tokens")
        
        return optimized_prompt, token_breakdown
    
    def _build_system_layer(self) -> str:
        """Build system instructions layer."""
        return """You are a helpful AI assistant with persistent memory.

Key capabilities:
- You remember user preferences and past conversations
- You learn from corrections and feedback
- You provide context-aware responses

Important guidelines:
- If you're unsure, say so
- Reference past conversations when relevant
- Acknowledge when you've been corrected before"""
    
    def _build_profile_layer(self, profile: Dict[str, Any]) -> str:
        """Build user profile layer."""
        if not profile:
            return ""
        
        prefs = profile.get("preferences", {})
        context = profile.get("context", {})
        
        return f"""

## User Profile
- Communication style: {prefs.get('communication_style', 'balanced')}
- Expertise level: {prefs.get('expertise_level', 'intermediate')}
- Interests: {', '.join(prefs.get('topics_of_interest', []))}
- Context: {context.get('occupation', 'Not specified')}"""
    
    def _build_feedback_layer(self, feedback_memory: Dict[str, Any]) -> str:
        """Build feedback corrections layer."""
        corrections = feedback_memory.get("corrections", [])
        
        if not corrections:
            return ""
        
        feedback_text = "\n\n## Past Corrections (Learn from these)"
        for correction in corrections[:3]:  # Top 3
            feedback_text += f"""
- Previous mistake: {correction.get('user_correction', '')}
- Correct approach: {correction.get('corrected_response', 'N/A')}"""
        
        return feedback_text
    
    def _build_summary_layer(self, summary: Dict[str, Any]) -> str:
        """Build conversation summary layer."""
        if not summary:
            return ""
        
        return f"""

## Conversation Summary
{summary.get('text', '')}
(Covers messages {summary.get('message_range_start', 0)} to {summary.get('message_range_end', 0)})"""
    
    def _build_semantic_layer(self, semantic_memory: Dict[str, Any]) -> str:
        """Build semantic context layer."""
        memories = semantic_memory.get("relevant_memories", [])
        
        if not memories:
            return ""
        
        context_text = "\n\n## Relevant Past Conversations"
        for memory in memories[:3]:  # Top 3
            metadata = memory.get("metadata", {})
            score = memory.get("similarity_score", 0)
            content = memory.get("content", "")[:200]  # Truncate
            
            context_text += f"""
- [{metadata.get('conversation_title', 'Untitled')}] (Similarity: {score:.2f})
  {content}..."""
        
        return context_text
    
    def _build_recent_messages_layer(self, short_term_memory: Dict[str, Any]) -> str:
        """Build recent messages layer."""
        messages = short_term_memory.get("messages", [])
        
        if not messages:
            return ""
        
        messages_text = "\n\n## Recent Conversation"
        for msg in messages[-10:]:  # Last 10
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            messages_text += f"\n{role}: {content}\n"
        
        return messages_text
    
    def _optimize_layers(self, layers: Dict[str, str]) -> tuple[str, Dict[str, int]]:
        """
        Optimize prompt to fit within token budget.
        
        Args:
            layers: Dictionary of prompt layers
            
        Returns:
            Tuple of (Optimized prompt string, layer_token_counts)
        """
        # Calculate current token usage
        layer_tokens = {
            name: token_manager.count_tokens(content)
            for name, content in layers.items()
        }
        
        total_tokens = sum(layer_tokens.values())
        available_tokens = settings.max_context_window - settings.response_buffer_tokens
        
        if total_tokens <= available_tokens:
            # No optimization needed
            return self._assemble_prompt(layers), layer_tokens
        
        logger.warning(
            f"Prompt exceeds budget: {total_tokens} > {available_tokens}. "
            "Trimming layers..."
        )
        
        # Trim layers based on priority (semantic first, then summary, etc.)
        trimmed_layers = layers.copy()
        
        # Trim semantic context
        if layer_tokens.get("semantic_context", 0) > self.TOKEN_ALLOCATION["semantic_context"]:
            trimmed_layers["semantic_context"] = token_manager.truncate(
                layers["semantic_context"],
                self.TOKEN_ALLOCATION["semantic_context"]
            )
        
        # Trim recent messages if still over budget
        total_after_trim = sum(
            token_manager.count_tokens(content)
            for content in trimmed_layers.values()
        )
        
        if total_after_trim > available_tokens:
            trimmed_layers["recent_messages"] = token_manager.truncate(
                layers["recent_messages"],
                self.TOKEN_ALLOCATION["recent_messages"]
            )
        
        # Recalculate token counts for trimmed layers
        final_tokens = {
            name: token_manager.count_tokens(content)
            for name, content in trimmed_layers.items()
        }
        
        return self._assemble_prompt(trimmed_layers), final_tokens
    
    def _assemble_prompt(self, layers: Dict[str, str]) -> str:
        """Assemble layers in correct order."""
        prompt_parts = [
            layers.get(layer_name, "")
            for layer_name in self.LAYER_ORDER
            if layers.get(layer_name)
        ]
        return "\n".join(prompt_parts)


# Global prompt builder instance
prompt_builder = PromptBuilder()
