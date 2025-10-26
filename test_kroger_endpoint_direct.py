#!/usr/bin/env python3
"""
Test the /grocery/from-recipe endpoint which has direct Kroger API integration
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_grocery_from_recipe_endpoint():
    """Test the /grocery/from-recipe endpoint with direct Kroger API calls"""
    
    print("🧪 Testing /grocery/from-recipe Endpoint")
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
        "email": f"krogertest{int(datetime.now().timestamp())}@example.com",
        "username": f"krogertest{int(datetime.now().timestamp())}",
        "password": "TestPass123!",
        "name": "Kroger Test User",
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
    
    # Test /grocery/from-recipe endpoint
    print("\n🛒 Testing /grocery/from-recipe endpoint...")
    
    # Create test recipe with ingredients
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
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            "http://localhost:8000/grocery/from-recipe",
            json=test_recipe,
            headers=headers,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ /grocery/from-recipe endpoint successful!")
            print(f"Store: {data.get('store', 'N/A')}")
            print(f"Total items: {data.get('total_items', 0)}")
            print(f"Kroger items found: {data.get('kroger_items_found', 0)}")
            print(f"Total cost: ${data.get('total_estimated_cost', 0)}")
            print(f"LLM Provider: {data.get('llm_provider', 'N/A')}")
            
            # Print detailed item information
            print("\n📋 Detailed item breakdown:")
            items = data.get("items", [])
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item.get('name', 'Unknown')}")
                print(f"     Quantity: {item.get('quantity', 'N/A')}")
                print(f"     Price: ${item.get('estimated_price', 0)}")
                print(f"     Category: {item.get('category', 'N/A')}")
                if item.get('product_id'):
                    print(f"     ✅ Kroger Product ID: {item['product_id']}")
                if item.get('brand'):
                    print(f"     Brand: {item['brand']}")
                if item.get('upc'):
                    print(f"     UPC: {item['upc']}")
                print()
            
            return True
        else:
            print(f"❌ /grocery/from-recipe failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ /grocery/from-recipe error: {e}")
        return False

if __name__ == "__main__":
    success = test_grocery_from_recipe_endpoint()
    if success:
        print("\n🎉 /grocery/from-recipe endpoint test PASSED!")
    else:
        print("\n❌ /grocery/from-recipe endpoint test FAILED!")
    sys.exit(0 if success else 1)
