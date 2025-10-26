#!/usr/bin/env python3
"""
Direct database test to isolate the registration issue
"""

from database import get_db, User, UserProfile, init_db
from auth import create_access_token
from datetime import timedelta

def test_direct_registration():
    """Test registration logic directly without FastAPI"""
    print("🧪 Testing direct database registration...")
    
    try:
        # Initialize database
        init_db()
        print("✅ Database initialized")
        
        # Get database session
        db = next(get_db())
        print("✅ Database session created")
        
        # Test data
        user_data = {
            "email": "direct@example.com",
            "username": "directuser",
            "name": "Direct User",
            "password": "password123",
            "daily_calories": 2000.0,
            "dietary_restrictions": ["vegetarian"],
            "likes": ["spicy"],
            "additional_information": "Test user"
        }
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print("⚠️ User already exists, deleting...")
            db.delete(existing_user)
            db.commit()
        
        # Create user
        print("Creating user...")
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            name=user_data["name"],
            hashed_password=User.hash_password(user_data["password"])
        )
        db.add(user)
        db.flush()
        print(f"✅ User created with ID: {user.id}")
        
        # Create profile
        print("Creating profile...")
        profile = UserProfile(
            user_id=user.id,
            daily_calories=user_data["daily_calories"],
            dietary_restrictions=user_data["dietary_restrictions"],
            likes=user_data["likes"],
            additional_information=user_data["additional_information"]
        )
        db.add(profile)
        db.commit()
        print("✅ Profile created")
        
        # Test token creation
        print("Creating token...")
        token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=60)
        )
        print(f"✅ Token created: {token[:20]}...")
        
        # Clean up
        print("Cleaning up...")
        db.delete(profile)
        db.delete(user)
        db.commit()
        print("✅ Cleanup complete")
        
        print("🎉 Direct registration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Direct registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_direct_registration()
