from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    """User model for authentication and subscription management."""
    __tablename__ = "users"
    
    id = mapped_column(Integer, primary_key=True, index=True)
    user_id = mapped_column(String(255), unique=True, nullable=False, index=True)
    email = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password = mapped_column(String(255), nullable=False)
    full_name = mapped_column(String(255))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = mapped_column(Boolean, default=True)
    subscription_tier = mapped_column(String(50), default="free")  # free, pro, enterprise
    total_tokens_used = mapped_column(Integer, default=0)
    monthly_tokens_used = mapped_column(Integer, default=0)
    last_token_reset = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    feedback_corrections = relationship("FeedbackCorrection", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model for grouping messages."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_archived = Column(Boolean, default=False)
    total_messages = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    summaries = relationship("ConversationSummary", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for storing individual chat messages."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    conversation_id = Column(String(255), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    embedding_id = Column(String(255), index=True)  # Reference to ChromaDB
    message_metadata = Column(JSON)  # Additional context
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class UserProfile(Base):
    """User profile model for long-term memory."""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    profile_data = Column(JSON, nullable=False)  # Structured user preferences
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")


class FeedbackCorrection(Base):
    """Feedback correction model for learning from mistakes."""
    __tablename__ = "feedback_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(255), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(255), ForeignKey("messages.message_id", ondelete="CASCADE"), nullable=False)
    correction_type = Column(String(50), nullable=False)  # factual_error, tone_issue, irrelevant
    user_correction = Column(Text)  # What user said was wrong
    corrected_response = Column(Text)  # What should have been said
    context_snapshot = Column(JSON)  # Memory state at time of error
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    applied_count = Column(Integer, default=0)  # How many times this correction influenced responses
    
    # Relationships
    user = relationship("User", back_populates="feedback_corrections")


class ConversationSummary(Base):
    """Conversation summary model for token optimization."""
    __tablename__ = "conversation_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(String(255), unique=True, nullable=False, index=True)
    conversation_id = Column(String(255), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    message_range_start = Column(Integer, nullable=False)  # First message index in summary
    message_range_end = Column(Integer, nullable=False)  # Last message index in summary
    tokens_saved = Column(Integer, default=0)  # Tokens saved by summarization
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="summaries")


class MemoryAccessLog(Base):
    """Memory access log model for observability."""
    __tablename__ = "memory_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(255), nullable=False)
    request_id = Column(String(255), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)  # short_term, long_term, semantic, feedback
    access_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    items_retrieved = Column(Integer, default=0)
    retrieval_time_ms = Column(Float)
    access_metadata = Column(JSON)  # Memory-specific details


class RequestTrace(Base):
    """Request trace model for full request lifecycle tracking."""
    __tablename__ = "request_traces"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(255), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    latency_ms = Column(Float)
    llm_provider = Column(String(50))  # openai, claude
    model_name = Column(String(100))
    memory_snapshot = Column(JSON)  # Full memory state for this request
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
