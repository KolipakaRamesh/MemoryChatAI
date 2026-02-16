from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Environment
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///./data/memorychat.db"
    
    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_enabled: bool = False  # Disable for MVP
    
    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Encryption
    encryption_key: str
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    default_llm_provider: str = "groq"
    default_model: str = "llama-3.3-70b-versatile"
    
    # Embedding Service
    embedding_model: str = "text-embedding-ada-002"
    
    # Rate Limiting
    rate_limit_free: str = "10/minute"
    rate_limit_pro: str = "100/minute"
    rate_limit_enterprise: str = "1000/minute"
    
    # Token Limits
    max_context_window: int = 4096
    response_buffer_tokens: int = 1000
    summarization_threshold_tokens: int = 2000
    
    # Memory Configuration
    max_short_term_messages: int = 20
    max_semantic_results: int = 5
    semantic_similarity_threshold: float = 0.7
    max_feedback_corrections: int = 3
    
    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = True
    log_level: str = "INFO"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
