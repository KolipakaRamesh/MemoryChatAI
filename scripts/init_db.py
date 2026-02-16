#!/usr/bin/env python3
"""
Initialize database with sample data for testing.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.session import engine, Base
from backend.app.models.database import User, UserProfile
from sqlalchemy.orm import sessionmaker
import uuid

def init_db():
    """Initialize database with tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

def seed_demo_user():
    """Create a demo user for testing."""
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Check if demo user exists
        existing_user = db.query(User).filter(User.user_id == "demo_user_123").first()
        
        if existing_user:
            print("✓ Demo user already exists")
            return
        
        # Create demo user
        demo_user = User(
            user_id="demo_user_123",
            email="demo@memorychat.ai",
            hashed_password="demo_password_hash",  # In production, use proper hashing
            full_name="Demo User",
            subscription_tier="pro"
        )
        
        db.add(demo_user)
        db.commit()
        
        # Create default profile
        demo_profile = UserProfile(
            user_id="demo_user_123",
            profile_data={
                "preferences": {
                    "communication_style": "technical",
                    "expertise_level": "senior",
                    "topics_of_interest": ["AI", "SaaS", "Architecture"]
                },
                "behavior_patterns": {
                    "typical_session_length": 0,
                    "preferred_response_length": "medium",
                    "frequently_asked_topics": []
                },
                "context": {
                    "occupation": "Software Architect",
                    "timezone": "UTC+5:30",
                    "language": "en"
                }
            }
        )
        
        db.add(demo_profile)
        db.commit()
        
        print("✓ Demo user created: demo@memorychat.ai")
        print("  User ID: demo_user_123")
        print("  Tier: pro")
        
    except Exception as e:
        print(f"✗ Error creating demo user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing MemoryChatAI Database...")
    print("=" * 50)
    
    init_db()
    seed_demo_user()
    
    print("=" * 50)
    print("✓ Database initialization complete!")
    print("\nYou can now start the server with:")
    print("  cd backend")
    print("  python -m app.main")
