#!/usr/bin/env python3
"""
Test both grocery endpoints to compare their behavior
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_both_endpoints():
    """Test both /grocery and /grocery/from-recipe endpoints"""
    
    print("🧪 Testing Both Grocery Endpoints")
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
    
    # Test recipe data
    test_recipe = {
        "title": "Test Paneer Curry",
        "description": "A test recipe for Kroger API",
        "ingredients": [
            {"name": "paneer", "quantity": 200, "unit": "g"},
            {"name": "milk", "quantity": 1, "unit": "gallon"},
            {"name": "quinoa", "quantity": 1, "unit": "cup"},
            {"name": "ghee", "quantity": 2, "unit": "tbsp"},
            {"name": "garam masala", "quantity": 1, "unit": "tsp"}
        ]
    }
    
    # Test 1: /grocery endpoint
    print("\n🛒 Test 1: /grocery endpoint")
    print("-" * 40)
    
    grocery_request = {
        "recipe": test_recipe,
        "user_id": "test_user",
        "store_preference": "Kroger"
    }
    
    try:
        response1 = requests.post(
            "http://localhost:8000/grocery",
            json=grocery_request,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response1.status_code}")
        
        if response1.status_code == 200:
            data1 = response1.json()
            print("✅ /grocery endpoint successful!")
            print(f"Store: {data1.get('store', 'N/A')}")
            print(f"Total items: {data1.get('total_items', 0)}")
            print(f"Kroger items found: {data1.get('kroger_items_found', 0)}")
            print(f"Total cost: ${data1.get('total_estimated_cost', 0)}")
            print(f"LLM Provider: {data1.get('llm_provider', 'N/A')}")
            
            # Show first few items
            items1 = data1.get("items", [])
            print(f"\nFirst 3 items from /grocery:")
            for i, item in enumerate(items1[:3], 1):
                print(f"  {i}. {item.get('name', 'Unknown')} - ${item.get('estimated_price', 0)}")
                if item.get('product_id'):
                    print(f"     ✅ Product ID: {item['product_id']}")
        else:
            print(f"❌ /grocery failed: {response1.status_code}")
            print(f"Response: {response1.text}")
            
    except Exception as e:
        print(f"❌ /grocery error: {e}")
    
    # Test 2: /grocery/from-recipe endpoint
    print("\n🛒 Test 2: /grocery/from-recipe endpoint")
    print("-" * 40)
    
    try:
        response2 = requests.post(
            "http://localhost:8000/grocery/from-recipe",
            json=test_recipe,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            print("✅ /grocery/from-recipe endpoint successful!")
            print(f"Store: {data2.get('store', 'N/A')}")
            print(f"Total items: {data2.get('total_items', 0)}")
            print(f"Kroger items found: {data2.get('kroger_items_found', 0)}")
            print(f"Total cost: ${data2.get('total_estimated_cost', 0)}")
            print(f"LLM Provider: {data2.get('llm_provider', 'N/A')}")
            
            # Show first few items
            items2 = data2.get("items", [])
            print(f"\nFirst 3 items from /grocery/from-recipe:")
            for i, item in enumerate(items2[:3], 1):
                price = item.get('total_price', item.get('estimated_price', 0))
                print(f"  {i}. {item.get('name', 'Unknown')} - ${price}")
                if item.get('kroger_product_id'):
                    print(f"     ✅ Product ID: {item['kroger_product_id']}")
        else:
            print(f"❌ /grocery/from-recipe failed: {response2.status_code}")
            print(f"Response: {response2.text}")
            
    except Exception as e:
        print(f"❌ /grocery/from-recipe error: {e}")
    
    # Summary
    print("\n📊 Summary:")
    print("=" * 60)
    print("Both endpoints should work, but:")
    print("- /grocery uses generate_grocery_list() → create_grocery_list() → search_and_price_ingredient()")
    print("- /grocery/from-recipe uses direct Kroger API calls")
    print("- If Kroger API is unavailable, both should fall back to estimated pricing")
    
    return True

if __name__ == "__main__":
    test_both_endpoints()
