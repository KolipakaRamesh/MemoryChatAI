import tiktoken
from typing import Dict, Any
from app.config import settings
from app.observability.logger import get_logger

logger = get_logger(__name__)


class TokenManager:
    """Token counting and optimization manager."""
    
    def __init__(self):
        # Initialize tiktoken encoder
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        
        self.max_context_window = settings.max_context_window
        self.response_buffer = settings.response_buffer_tokens
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Input text
            
        Returns:
            Token count
        """
        try:
            tokens = self.encoder.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
    
    def truncate(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to maximum token count.
        
        Args:
            text: Input text
            max_tokens: Maximum allowed tokens
            
        Returns:
            Truncated text
        """
        try:
            tokens = self.encoder.encode(text)
            
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate and decode
            truncated_tokens = tokens[:max_tokens]
            return self.encoder.decode(truncated_tokens)
            
        except Exception as e:
            logger.error(f"Error truncating text: {e}")
            # Fallback: character-based truncation
            return text[:max_tokens * 4]
    
    def estimate_tokens(self, memory_snapshot: Dict[str, Any]) -> int:
        """
        Estimate total tokens in memory snapshot.
        
        Args:
            memory_snapshot: Memory data
            
        Returns:
            Estimated token count
        """
        total_tokens = 0
        
        # Count short-term memory tokens
        stm = memory_snapshot.get("short_term_memory", {})
        for msg in stm.get("messages", []):
            total_tokens += msg.get("tokens", 0)
        
        # Count summary tokens
        if stm.get("summary"):
            summary_text = stm["summary"].get("text", "")
            total_tokens += self.count_tokens(summary_text)
        
        # Estimate other memory types (rough approximation)
        ltm = memory_snapshot.get("long_term_memory", {})
        if ltm:
            total_tokens += 200  # Approximate profile size
        
        sem = memory_snapshot.get("semantic_memory", {})
        for memory in sem.get("relevant_memories", []):
            total_tokens += self.count_tokens(memory.get("content", ""))
        
        fbm = memory_snapshot.get("feedback_memory", {})
        for correction in fbm.get("corrections", []):
            total_tokens += self.count_tokens(correction.get("user_correction", ""))
        
        return total_tokens
    
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4"
    ) -> float:
        """
        Calculate cost for LLM API call.
        
        Args:
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            model: Model name
            
        Returns:
            Cost in USD
        """
        # Pricing per 1K tokens (as of 2024)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075}
        }
        
        model_pricing = pricing.get(model, pricing["gpt-4"])
        
        cost = (
            (prompt_tokens / 1000) * model_pricing["input"] +
            (completion_tokens / 1000) * model_pricing["output"]
        )
        
        return round(cost, 6)


# Global token manager instance
token_manager = TokenManager()
