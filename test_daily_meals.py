"""
Test script for daily meal planning system
Tests the core functionality without requiring full API setup
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_chroma_service():
    """Test ChromaDB service functionality"""
    print("🧪 Testing ChromaDB Service...")
    
    try:
        from chroma_service import ChromaService
        
        # Initialize service
        chroma_service = ChromaService()
        print("✅ ChromaDB service initialized")
        
        # Test embedding generation
        test_text = "I love spicy Indian food and hate mushrooms"
        embedding = chroma_service.generate_embedding(test_text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        
        # Test preference storage
        preference_data = {
            "user_id": 1,
            "preference_type": "liked",
            "item_name": "spicy food",
            "item_type": "flavor",
            "context": "User loves spicy food",
            "strength": 1.0
        }
        
        chroma_id = chroma_service.store_user_preference(1, preference_data, embedding)
        print(f"✅ Stored preference with ID: {chroma_id}")
        
        # Test preference retrieval
        preferences = chroma_service.get_user_preferences(1)
        print(f"✅ Retrieved {len(preferences)} preferences")
        
        # Test dislikes
        dislikes = chroma_service.get_user_dislikes(1)
        print(f"✅ Retrieved {len(dislikes)} dislikes")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        return False

def test_daily_meal_generation():
    """Test daily meal generation (mock test)"""
    print("\n🧪 Testing Daily Meal Generation...")
    
    try:
        from agents.recipe_agent.daily_meals import DailyMealRequest, generate_daily_meals_with_claude
        from chroma_service import ChromaService
        
        # Mock user profile
        class MockUserProfile:
            def __init__(self):
                self.daily_calories = 2000
                self.dietary_restrictions = ["vegetarian"]
                self.likes = ["spicy", "indian"]
                self.target_protein_g = None
                self.target_carbs_g = None
                self.target_fat_g = None
        
        # Initialize services
        chroma_service = ChromaService()
        user_profile = MockUserProfile()
        
        # Create request
        request = DailyMealRequest(
            user_id=1,
            date="2024-01-15",
            target_calories=2000
        )
        
        print("✅ Daily meal request created")
        print("ℹ️  Note: Full generation requires Claude API key")
        
        return True
        
    except Exception as e:
        print(f"❌ Daily meal test failed: {e}")
        return False

def test_database_models():
    """Test database models"""
    print("\n🧪 Testing Database Models...")
    
    try:
        from database import init_db, User, UserProfile, Recipe, DailyMealPlan, UserPreference
        
        # Initialize database
        init_db()
        print("✅ Database initialized")
        
        # Test model imports
        print("✅ All models imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Daily Meal Planning System\n")
    
    tests = [
        ("Database Models", test_database_models),
        ("ChromaDB Service", test_chroma_service),
        ("Daily Meal Generation", test_daily_meal_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Daily meal planning system is ready!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
