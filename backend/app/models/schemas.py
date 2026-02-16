from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class MessageRole(str, Enum):
    """Message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class CorrectionType(str, Enum):
    """Feedback correction types."""
    FACTUAL_ERROR = "factual_error"
    TONE_ISSUE = "tone_issue"
    IRRELEVANT = "irrelevant"


# Request/Response Schemas

class ChatMessageRequest(BaseModel):
    """Chat message request schema."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""
    response: str
    conversation_id: str
    message_id: str
    observability: Dict[str, Any]


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserProfileUpdate(BaseModel):
    """User profile update schema."""
    preferences: Optional[Dict[str, Any]] = None
    behavior_patterns: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class FeedbackCorrectionCreate(BaseModel):
    """Feedback correction creation schema."""
    message_id: str
    correction_type: CorrectionType
    user_correction: str
    corrected_response: Optional[str] = None


# Memory Schemas

class ShortTermMemory(BaseModel):
    """Short-term memory schema."""
    messages: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None


class LongTermMemory(BaseModel):
    """Long-term memory schema."""
    preferences: Dict[str, Any]
    behavior_patterns: Dict[str, Any]
    context: Dict[str, Any]
    last_updated: datetime


class SemanticMemory(BaseModel):
    """Semantic memory schema."""
    relevant_memories: List[Dict[str, Any]]


class FeedbackMemory(BaseModel):
    """Feedback memory schema."""
    corrections: List[Dict[str, Any]]


class TokenUsage(BaseModel):
    """Token usage schema."""
    breakdown: Dict[str, int]
    total: int
    estimated_response: int
    cost: float


class ObservabilityData(BaseModel):
    """Observability data schema."""
    request_id: str
    short_term_memory: ShortTermMemory
    long_term_memory: LongTermMemory
    semantic_memory: SemanticMemory
    feedback_memory: FeedbackMemory
    token_usage: TokenUsage
    request_trace: Dict[str, Any]


# Database Model Schemas

class UserSchema(BaseModel):
    """User schema for API responses."""
    user_id: str
    email: str
    full_name: Optional[str]
    subscription_tier: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationSchema(BaseModel):
    """Conversation schema for API responses."""
    conversation_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    total_messages: int
    total_tokens: int
    
    class Config:
        from_attributes = True


class MessageSchema(BaseModel):
    """Message schema for API responses."""
    message_id: str
    role: MessageRole
    content: str
    tokens_used: int
    created_at: datetime
    
    class Config:
        from_attributes = True
