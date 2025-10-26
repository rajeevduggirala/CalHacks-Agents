#!/usr/bin/env python3
"""
Debug script for registration issues
"""

import sys
import traceback
from database import init_db, get_db, create_user, get_user_by_email, get_user_by_username, User, UserProfile
from auth import create_access_token
from datetime import timedelta

def test_database_connection():
    """Test database connection and initialization"""
    print("🧪 Testing database connection...")
    try:
        init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        traceback.print_exc()
        return False

def test_user_creation():
    """Test user creation step by step"""
    print("\n🧪 Testing user creation...")
    
    try:
        # Get database session
        db = next(get_db())
        print("✅ Database session created")
        
        # Test password hashing
        test_password = "testpassword123"
        hashed = User.hash_password(test_password)
        print(f"✅ Password hashing works: {hashed[:20]}...")
        
        # Test user creation
        user_data = {
            "email": "debug@example.com",
            "username": "debuguser",
            "name": "Debug User",
            "password": test_password
        }
        
        # Check if user exists
        existing_user = get_user_by_email(db, user_data["email"])
        if existing_user:
            print("⚠️ User already exists, deleting...")
            db.delete(existing_user)
            db.commit()
        
        # Create user
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            name=user_data["name"],
            hashed_password=User.hash_password(user_data["password"])
        )
        print("✅ User object created")
        
        db.add(user)
        db.flush()
        print(f"✅ User added to database with ID: {user.id}")
        
        # Create profile
        profile = UserProfile(
            user_id=user.id,
            daily_calories=2000.0,
            dietary_restrictions=["vegetarian"],
            likes=["spicy"],
            additional_information="Test user"
        )
        print("✅ Profile object created")
        
        db.add(profile)
        db.commit()
        print("✅ Profile added to database")
        
        # Test token creation
        token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=60)
        )
        print(f"✅ Token created: {token[:20]}...")
        
        # Clean up
        db.delete(profile)
        db.delete(user)
        db.commit()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    """Main debug function"""
    print("🔍 Debugging Registration Issues")
    print("=" * 50)
    
    # Test 1: Database connection
    if not test_database_connection():
        print("\n❌ Database test failed. Cannot continue.")
        return
    
    # Test 2: User creation
    if not test_user_creation():
        print("\n❌ User creation test failed.")
        return
    
    print("\n🎉 All debug tests passed! Registration should work.")

if __name__ == "__main__":
    main()
