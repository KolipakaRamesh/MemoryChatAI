from typing import Optional, List
from abc import ABC, abstractmethod
import openai
import anthropic
from groq import Groq
from app.config import settings
from app.observability.logger import get_logger

logger = get_logger(__name__)


class BaseLLMService(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> dict:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass


class OpenAIService(BaseLLMService):
    """OpenAI LLM service implementation."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.default_model
        self.embedding_model = settings.embedding_model
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> dict:
        """
        Generate response using OpenAI API.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Dictionary with response and token usage
        """
        try:
            logger.info(f"Generating response with {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            result = {
                "response": response.choices[0].message.content,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": self.model,
                "provider": "openai"
            }
            
            logger.info(f"Generated response: {result['total_tokens']} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI API.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Generated embedding: {len(embedding)} dimensions")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise


class GroqService(BaseLLMService):
    """Groq LLM service implementation."""
    
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.default_model or "llama-3.3-70b-versatile"
        self._embedding_model = None
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> dict:
        """
        Generate response using Groq API.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Dictionary with response and token usage
        """
        try:
            logger.info(f"Generating response with Groq {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            result = {
                "response": response.choices[0].message.content,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": self.model,
                "provider": "groq"
            }
            
            logger.info(f"Generated response: {result['total_tokens']} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response with Groq: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using sentence-transformers (Groq doesn't provide embeddings).
        Using a lightweight model for fast local embeddings.
        """
        try:
            if self._embedding_model is None:
                from sentence_transformers import SentenceTransformer
                logger.info("Initializing SentenceTransformer model 'all-MiniLM-L6-v2'")
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            embedding = self._embedding_model.encode(text).tolist()
            
            logger.info(f"Generated embedding: {len(embedding)} dimensions")
            return embedding
            
        except ImportError:
            logger.warning("sentence-transformers not installed. Using simple hash-based fallback embedding.")
            # Simple deterministic fallback: use hash of text to create a repeatable 384-d vector
            import hashlib
            import numpy as np
            
            # Create a deterministic 384-dimensional vector based on the text hash
            h = hashlib.sha256(text.encode()).digest()
            # Use the hash as a seed for reproducibility
            np.random.seed(int.from_bytes(h[:4], "big"))
            embedding = np.random.uniform(-1, 1, 384).tolist()
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise


class AnthropicService(BaseLLMService):
    """Anthropic (Claude) LLM service implementation."""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-opus-20240229"
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> dict:
        """
        Generate response using Anthropic API.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Dictionary with response and token usage
        """
        try:
            logger.info(f"Generating response with {self.model}")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = {
                "response": message.content[0].text,
                "prompt_tokens": message.usage.input_tokens,
                "completion_tokens": message.usage.output_tokens,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
                "model": self.model,
                "provider": "anthropic"
            }
            
            logger.info(f"Generated response: {result['total_tokens']} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Anthropic doesn't provide embeddings, fallback to OpenAI."""
        openai_service = OpenAIService()
        return await openai_service.generate_embedding(text)


class LLMServiceFactory:
    """Factory for creating LLM service instances."""
    
    @staticmethod
    def create(provider: Optional[str] = None) -> BaseLLMService:
        """
        Create LLM service instance.
        
        Args:
            provider: LLM provider name (openai, anthropic, groq)
            
        Returns:
            LLM service instance
        """
        provider = provider or settings.default_llm_provider
        
        if provider == "openai":
            return OpenAIService()
        elif provider == "anthropic":
            return AnthropicService()
        elif provider == "groq":
            return GroqService()
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


# Global LLM service instance
llm_service = LLMServiceFactory.create()
