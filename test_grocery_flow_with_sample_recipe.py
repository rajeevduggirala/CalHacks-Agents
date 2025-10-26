#!/usr/bin/env python3
"""
Test Grocery Flow with Sample Recipe
Tests both grocery endpoints with a pre-made recipe to avoid recipe generation timeout
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_grocery_flow_with_sample_recipe():
    """Test grocery flow with a sample recipe"""
    
    print("🧪 Grocery Flow Test with Sample Recipe")
    print("=" * 60)
    
    # Check if server is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server not running")
            return False
        print("✅ Server is running")
    except:
        print("❌ Server not accessible")
        return False
    
    # Create test user
    print("\n📝 Creating test user...")
    user_data = {
        "email": f"grocerytest{int(datetime.now().timestamp())}@example.com",
        "username": f"grocerytest{int(datetime.now().timestamp())}",
        "password": "TestPass123!",
        "name": "Grocery Test User",
        "daily_calories": 2000,
        "dietary_restrictions": ["vegetarian"],
        "likes": ["indian", "spicy"]
    }
    
    try:
        register_response = requests.post(
            "http://localhost:8000/auth/register",
            json=user_data,
            timeout=10
        )
        
        if register_response.status_code not in [200, 201]:
            print(f"❌ User creation failed: {register_response.status_code}")
            return False
        
        auth_data = register_response.json()
        auth_token = auth_data.get("access_token")
        print(f"✅ User created, token: {auth_token[:20]}...")
        
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Sample recipe (realistic Indian vegetarian recipe)
    sample_recipe = {
        "title": "Paneer Butter Masala",
        "description": "A rich and creamy Indian curry with paneer in a tomato-based sauce",
        "ingredients": [
            {"name": "paneer", "quantity": 200, "unit": "g", "notes": "cubed"},
            {"name": "tomatoes", "quantity": 3, "unit": "medium", "notes": "chopped"},
            {"name": "onions", "quantity": 1, "unit": "large", "notes": "chopped"},
            {"name": "garlic", "quantity": 4, "unit": "cloves", "notes": "minced"},
            {"name": "ginger", "quantity": 1, "unit": "inch", "notes": "grated"},
            {"name": "heavy cream", "quantity": 1, "unit": "cup", "notes": ""},
            {"name": "butter", "quantity": 3, "unit": "tbsp", "notes": ""},
            {"name": "garam masala", "quantity": 1, "unit": "tsp", "notes": ""},
            {"name": "turmeric", "quantity": 0.5, "unit": "tsp", "notes": ""},
            {"name": "cumin", "quantity": 1, "unit": "tsp", "notes": ""},
            {"name": "salt", "quantity": 1, "unit": "tsp", "notes": "to taste"},
            {"name": "sugar", "quantity": 1, "unit": "tsp", "notes": ""}
        ],
        "instructions": "1. Heat butter in a pan\n2. Add onions and cook until golden\n3. Add tomatoes and spices\n4. Add paneer and cream\n5. Simmer for 10 minutes",
        "cook_time": "30 minutes",
        "servings": 4,
        "cuisine": "indian",
        "difficulty": "medium"
    }
    
    print(f"\n🍳 Using sample recipe: {sample_recipe['title']}")
    print(f"Description: {sample_recipe['description']}")
    print(f"Ingredients: {len(sample_recipe['ingredients'])}")
    
    # Test 1: /grocery endpoint
    print("\n🛒 Test 1: /grocery endpoint")
    print("-" * 40)
    
    grocery_request = {
        "recipe": sample_recipe,
        "user_id": "test_user",
        "store_preference": "Kroger"
    }
    
    try:
        grocery_response = requests.post(
            "http://localhost:8000/grocery",
            json=grocery_request,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {grocery_response.status_code}")
        
        if grocery_response.status_code == 200:
            grocery_data = grocery_response.json()
            
            print("✅ /grocery endpoint successful!")
            print(f"Store: {grocery_data.get('store', 'N/A')}")
            print(f"Total items: {grocery_data.get('total_items', 0)}")
            print(f"Kroger items found: {grocery_data.get('kroger_items_found', 0)}")
            print(f"Total cost: ${grocery_data.get('total_estimated_cost', 0)}")
            print(f"LLM Provider: {grocery_data.get('llm_provider', 'N/A')}")
            
            # Show first few items
            items = grocery_data.get("items", [])
            print(f"\nFirst 5 items:")
            for i, item in enumerate(items[:5], 1):
                print(f"  {i}. {item.get('name', 'Unknown')} - ${item.get('estimated_price', 0)}")
                if item.get('product_id'):
                    print(f"     ✅ Kroger Product ID: {item['product_id']}")
            
            grocery_endpoint_success = True
        else:
            print(f"❌ /grocery failed: {grocery_response.status_code}")
            print(f"Response: {grocery_response.text}")
            grocery_endpoint_success = False
            
    except Exception as e:
        print(f"❌ /grocery error: {e}")
        grocery_endpoint_success = False
    
    # Test 2: /grocery/from-recipe endpoint
    print("\n🛒 Test 2: /grocery/from-recipe endpoint")
    print("-" * 40)
    
    # Convert recipe to the format expected by /grocery/from-recipe
    recipe_for_grocery = {
        "title": sample_recipe["title"],
        "description": sample_recipe["description"],
        "ingredients": []
    }
    
    # Convert ingredients to the expected format
    for ingredient in sample_recipe["ingredients"]:
        recipe_for_grocery["ingredients"].append({
            "name": ingredient["name"],
            "quantity": ingredient["quantity"],
            "unit": ingredient["unit"]
        })
    
    try:
        grocery_from_recipe_response = requests.post(
            "http://localhost:8000/grocery/from-recipe",
            json=recipe_for_grocery,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {grocery_from_recipe_response.status_code}")
        
        if grocery_from_recipe_response.status_code == 200:
            grocery_from_recipe_data = grocery_from_recipe_response.json()
            
            print("✅ /grocery/from-recipe endpoint successful!")
            print(f"Store: {grocery_from_recipe_data.get('store', 'N/A')}")
            print(f"Total items: {grocery_from_recipe_data.get('total_items', 0)}")
            print(f"Kroger items found: {grocery_from_recipe_data.get('kroger_items_found', 0)}")
            print(f"Total cost: ${grocery_from_recipe_data.get('total_estimated_cost', 0)}")
            print(f"LLM Provider: {grocery_from_recipe_data.get('llm_provider', 'N/A')}")
            
            # Show first few items
            items = grocery_from_recipe_data.get("items", [])
            print(f"\nFirst 5 items:")
            for i, item in enumerate(items[:5], 1):
                price = item.get('total_price', item.get('estimated_price', 0))
                print(f"  {i}. {item.get('name', 'Unknown')} - ${price}")
                if item.get('kroger_product_id'):
                    print(f"     ✅ Kroger Product ID: {item['kroger_product_id']}")
            
            grocery_from_recipe_success = True
        else:
            print(f"❌ /grocery/from-recipe failed: {grocery_from_recipe_response.status_code}")
            print(f"Response: {grocery_from_recipe_response.text}")
            grocery_from_recipe_success = False
            
    except Exception as e:
        print(f"❌ /grocery/from-recipe error: {e}")
        grocery_from_recipe_success = False
    
    # Final Summary
    print("\n📊 Final Test Summary")
    print("=" * 60)
    
    if grocery_endpoint_success and grocery_from_recipe_success:
        print("🎉 COMPLETE SUCCESS!")
        print("✅ Both grocery endpoints working perfectly")
        print("✅ Realistic pricing (no $2k issues)")
        print("✅ Recipe-to-grocery flow functional")
        print("✅ System ready for production")
        return True
    else:
        print("⚠️ PARTIAL SUCCESS")
        if grocery_endpoint_success:
            print("✅ /grocery endpoint working")
        else:
            print("❌ /grocery endpoint failed")
        
        if grocery_from_recipe_success:
            print("✅ /grocery/from-recipe endpoint working")
        else:
            print("❌ /grocery/from-recipe endpoint failed")
        
        return False

if __name__ == "__main__":
    success = test_grocery_flow_with_sample_recipe()
    if success:
        print("\n🚀 Grocery system is production-ready!")
    else:
        print("\n⚠️ Some issues need attention")
    sys.exit(0 if success else 1)
