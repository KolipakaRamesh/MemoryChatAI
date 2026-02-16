from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.memory.base import BaseMemory
from app.models.database import UserProfile
from app.observability.logger import get_logger

logger = get_logger(__name__)


class LongTermMemory(BaseMemory):
    """Long-term memory implementation for user profiles."""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}  # In-memory cache (Redis in production)
    
    async def retrieve(
        self, 
        user_id: str, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Retrieve user profile from cache or database.
        
        Args:
            user_id: User identifier
            db: Database session
            
        Returns:
            User profile dictionary
        """
        logger.info(f"Retrieving long-term memory for user: {user_id}")
        
        # Check cache
        if user_id in self.cache:
            logger.info(f"Retrieved profile from cache for user: {user_id}")
            return self.cache[user_id]
        
        # Query database
        profile_record = db.query(UserProfile)\
            .filter(UserProfile.user_id == user_id)\
            .first()
        
        if not profile_record:
            # Create default profile
            profile = self._create_default_profile()
            logger.info(f"Created default profile for user: {user_id}")
        else:
            profile = profile_record.profile_data
            logger.info(f"Retrieved profile from database for user: {user_id}")
        
        # Cache the profile
        self.cache[user_id] = profile
        
        return profile
    
    async def store(
        self, 
        user_id: str, 
        profile_data: Dict[str, Any],
        db: Session
    ) -> None:
        """
        Store or update user profile.
        
        Args:
            user_id: User identifier
            profile_data: Profile data to store
            db: Database session
        """
        logger.info(f"Storing long-term memory for user: {user_id}")
        
        # Check if profile exists
        profile_record = db.query(UserProfile)\
            .filter(UserProfile.user_id == user_id)\
            .first()
        
        if profile_record:
            # Update existing profile
            profile_record.profile_data = profile_data
        else:
            # Create new profile
            profile_record = UserProfile(
                user_id=user_id,
                profile_data=profile_data
            )
            db.add(profile_record)
        
        db.commit()
        
        # Update cache
        self.cache[user_id] = profile_data
        
        logger.info(f"Stored profile for user: {user_id}")
    
    async def clear(self, user_id: str) -> None:
        """
        Clear cached profile for a user.
        
        Args:
            user_id: User identifier
        """
        if user_id in self.cache:
            del self.cache[user_id]
            logger.info(f"Cleared cache for user: {user_id}")
    
    def _create_default_profile(self) -> Dict[str, Any]:
        """Create default user profile."""
        from datetime import datetime, timezone
        return {
            "preferences": {
                "communication_style": "balanced",
                "expertise_level": "intermediate",
                "topics_of_interest": []
            },
            "behavior_patterns": {
                "typical_session_length": 0,
                "preferred_response_length": "medium",
                "frequently_asked_topics": []
            },
            "context": {
                "occupation": None,
                "timezone": "UTC",
                "language": "en"
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    async def update_profile(
        self, 
        user_id: str, 
        updates: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Update specific fields in user profile.
        
        Args:
            user_id: User identifier
            updates: Dictionary of updates to apply
            db: Database session
            
        Returns:
            Updated profile
        """
        # Get current profile
        profile = await self.retrieve(user_id, db)
        
        # Deep merge updates
        updated_profile = self._deep_merge(profile, updates)
        
        # Store updated profile
        await self.store(user_id, updated_profile, db)
        
        return updated_profile
    
    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
