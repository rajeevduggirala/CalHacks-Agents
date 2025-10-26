#!/usr/bin/env python3
"""
Comprehensive Kroger API Test Script
Tests all Kroger-related functionality and prints detailed results to console
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_separator(title=""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    else:
        print(f"\n{'-'*60}")

def print_result(item, status="info"):
    """Print formatted result"""
    icons = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
    print(f"{icons.get(status, 'ℹ️')} {item}")

def test_direct_kroger_api():
    """Test Kroger API directly with curl-like requests"""
    print_separator("Direct Kroger API Test")
    
    # Get credentials
    client_id = os.getenv("KROGER_CLIENT_ID")
    client_secret = os.getenv("KROGER_CLIENT_SECRET")
    location_id = os.getenv("KROGER_LOCATION_ID", "01400441")
    
    if not client_id or not client_secret:
        print_result("❌ Kroger credentials not found", "error")
        return False
    
    print_result(f"Client ID: {client_id[:10]}...", "info")
    print_result(f"Location ID: {location_id}", "info")
    
    # Test 1: Get token
    print_result("Step 1: Getting OAuth token...", "info")
    
    import base64
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    token_response = requests.post(
        "https://api.kroger.com/v1/connect/oauth2/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_base64}"
        },
        data={
            "grant_type": "client_credentials",
            "scope": "product.compact"
        },
        timeout=10
    )
    
    if token_response.status_code != 200:
        print_result(f"❌ Token request failed: {token_response.status_code}", "error")
        print_result(f"Response: {token_response.text}", "error")
        return False
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    print_result(f"✅ Token obtained: {access_token[:20]}...", "success")
    
    # Test 2: Search for products
    print_result("Step 2: Testing product search...", "info")
    
    test_products = ["milk", "bread", "paneer", "quinoa", "ghee"]
    
    for product in test_products:
        print_result(f"Searching for: {product}", "info")
        
        search_response = requests.get(
            "https://api.kroger.com/v1/products",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-cache"
            },
            params={
                "filter.term": product,
                "filter.locationId": location_id,
                "filter.limit": 3
            },
            timeout=10
        )
        
        if search_response.status_code == 200:
            data = search_response.json()
            products = data.get("data", [])
            
            if products:
                best_product = products[0]
                items = best_product.get("items", [])
                price = None
                
                if items and items[0].get("price"):
                    price_data = items[0]["price"]
                    price = price_data.get("regular", price_data.get("promo"))
                
                print_result(f"  ✅ Found: {best_product.get('description', 'Unknown')}", "success")
                print_result(f"     Price: ${price}", "success")
                print_result(f"     Brand: {best_product.get('brand', 'N/A')}", "success")
                print_result(f"     Product ID: {best_product.get('productId', 'N/A')}", "success")
                if items:
                    print_result(f"     Size: {items[0].get('size', 'N/A')}", "success")
            else:
                print_result(f"  ⚠️ No products found", "warning")
        else:
            print_result(f"  ❌ Search failed: {search_response.status_code}", "error")
    
    return True

def test_grocery_agent_functions():
    """Test grocery agent functions directly"""
    print_separator("Grocery Agent Functions Test")
    
    try:
        from agents.grocery_agent.agent import (
            get_kroger_token, 
            search_kroger_product, 
            search_and_price_ingredient,
            create_grocery_list
        )
        
        # Test token generation
        print_result("Testing get_kroger_token()...", "info")
        token = get_kroger_token()
        if token:
            print_result(f"✅ Token: {token[:20]}...", "success")
        else:
            print_result("❌ Token generation failed", "error")
            return False
        
        # Test product search
        print_result("Testing search_kroger_product()...", "info")
        test_ingredients = ["milk", "paneer", "quinoa", "ghee", "garam masala"]
        
        for ingredient in test_ingredients:
            print_result(f"Searching for: {ingredient}", "info")
            result = search_kroger_product(ingredient)
            
            if result and result.get("price"):
                print_result(f"  ✅ Found: {result['name']}", "success")
                print_result(f"     Price: ${result['price']}", "success")
                print_result(f"     Brand: {result.get('brand', 'N/A')}", "success")
                print_result(f"     Product ID: {result.get('product_id', 'N/A')}", "success")
                if result.get('size'):
                    print_result(f"     Size: {result['size']}", "success")
            else:
                print_result(f"  ⚠️ Not found or no price", "warning")
        
        # Test ingredient pricing
        print_result("Testing search_and_price_ingredient()...", "info")
        test_ingredient = ("paneer", 200, "g")
        result = search_and_price_ingredient(*test_ingredient)
        
        print_result(f"Result for {test_ingredient[0]}:", "info")
        print_result(f"  Name: {result['name']}", "info")
        print_result(f"  Price: ${result['price']}", "info")
        print_result(f"  Source: {result['source']}", "info")
        print_result(f"  Product ID: {result.get('product_id', 'N/A')}", "info")
        
        return True
        
    except ImportError as e:
        print_result(f"❌ Import error: {e}", "error")
        return False
    except Exception as e:
        print_result(f"❌ Error: {e}", "error")
        return False

def test_grocery_endpoint():
    """Test the grocery endpoint through the API"""
    print_separator("Grocery Endpoint Test")
    
    # Check if server is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code != 200:
            print_result("❌ Server not running", "error")
            return False
        print_result("✅ Server is running", "success")
    except:
        print_result("❌ Server not accessible", "error")
        return False
    
    # Create test user
    print_result("Creating test user...", "info")
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
            print_result(f"❌ User creation failed: {register_response.status_code}", "error")
            return False
        
        auth_data = register_response.json()
        auth_token = auth_data.get("access_token")
        print_result(f"✅ User created, token: {auth_token[:20]}...", "success")
        
    except Exception as e:
        print_result(f"❌ User creation error: {e}", "error")
        return False
    
    # Test grocery endpoint
    print_result("Testing grocery endpoint...", "info")
    
    test_recipe = {
        "title": "Test Paneer Curry",
        "description": "A test recipe for Kroger API",
        "ingredients": [
            {"name": "paneer", "quantity": 200, "unit": "g", "notes": "cubed"},
            {"name": "milk", "quantity": 1, "unit": "gallon", "notes": None},
            {"name": "quinoa", "quantity": 1, "unit": "cup", "notes": "uncooked"},
            {"name": "ghee", "quantity": 2, "unit": "tbsp", "notes": None},
            {"name": "garam masala", "quantity": 1, "unit": "tsp", "notes": None}
        ]
    }
    
    grocery_request = {
        "recipe": test_recipe,
        "user_id": "test_user",
        "store_preference": "Kroger"
    }
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        grocery_response = requests.post(
            "http://localhost:8000/grocery",
            json=grocery_request,
            headers=headers,
            timeout=30
        )
        
        if grocery_response.status_code == 200:
            data = grocery_response.json()
            
            print_result("✅ Grocery endpoint successful!", "success")
            print_result(f"Store: {data.get('store', 'N/A')}", "info")
            print_result(f"Total items: {data.get('total_items', 0)}", "info")
            print_result(f"Kroger items found: {data.get('kroger_items_found', 0)}", "info")
            print_result(f"Total cost: ${data.get('total_estimated_cost', 0)}", "info")
            print_result(f"LLM Provider: {data.get('llm_provider', 'N/A')}", "info")
            
            # Print detailed item information
            print_result("Detailed item breakdown:", "info")
            items = data.get("items", [])
            for i, item in enumerate(items, 1):
                print_result(f"  {i}. {item.get('name', 'Unknown')}", "info")
                print_result(f"     Quantity: {item.get('quantity', 'N/A')}", "info")
                print_result(f"     Price: ${item.get('estimated_price', 0)}", "info")
                print_result(f"     Category: {item.get('category', 'N/A')}", "info")
                if item.get('product_id'):
                    print_result(f"     Product ID: {item['product_id']}", "info")
                if item.get('brand'):
                    print_result(f"     Brand: {item['brand']}", "info")
            
            return True
        else:
            print_result(f"❌ Grocery endpoint failed: {grocery_response.status_code}", "error")
            print_result(f"Response: {grocery_response.text}", "error")
            return False
            
    except Exception as e:
        print_result(f"❌ Grocery endpoint error: {e}", "error")
        return False

def test_complete_recipe_to_grocery_flow():
    """Test the complete flow: recipe generation -> grocery list"""
    print_separator("Complete Recipe-to-Grocery Flow Test")
    
    # Check if server is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code != 200:
            print_result("❌ Server not running", "error")
            return False
    except:
        print_result("❌ Server not accessible", "error")
        return False
    
    # Create test user
    print_result("Creating test user for complete flow...", "info")
    user_data = {
        "email": f"flowtest{int(datetime.now().timestamp())}@example.com",
        "username": f"flowtest{int(datetime.now().timestamp())}",
        "password": "TestPass123!",
        "name": "Flow Test User",
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
            print_result(f"❌ User creation failed: {register_response.status_code}", "error")
            return False
        
        auth_data = register_response.json()
        auth_token = auth_data.get("access_token")
        print_result(f"✅ User created", "success")
        
    except Exception as e:
        print_result(f"❌ User creation error: {e}", "error")
        return False
    
    # Step 1: Generate recipe
    print_result("Step 1: Generating recipe...", "info")
    
    recipe_request = {
        "user_profile": {
            "target_macros": {"protein_g": 100, "carbs_g": 200, "fat_g": 50, "calories": 2000},
            "likes": ["indian", "spicy"],
            "dislikes": []
        },
        "preferences": {
            "meal_type": "lunch",
            "cuisine": "indian",
            "dietary_restrictions": "vegetarian",
            "cook_time": "30-45 mins"
        }
    }
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        recipe_response = requests.post(
            "http://localhost:8000/recipe",
            json=recipe_request,
            headers=headers,
            timeout=30
        )
        
        if recipe_response.status_code == 200:
            recipe_data = recipe_response.json()
            recipes = recipe_data.get("recipes", [])
            
            if recipes:
                selected_recipe = recipes[0]
                print_result(f"✅ Generated recipe: {selected_recipe.get('title', 'Unknown')}", "success")
                print_result(f"Description: {selected_recipe.get('description', 'N/A')}", "info")
                print_result(f"Ingredients: {len(selected_recipe.get('ingredients', []))}", "info")
                
                # Step 2: Create grocery list
                print_result("Step 2: Creating grocery list...", "info")
                
                grocery_request = {
                    "recipe": selected_recipe,
                    "user_id": "test_user",
                    "store_preference": "Kroger"
                }
                
                grocery_response = requests.post(
                    "http://localhost:8000/grocery",
                    json=grocery_request,
                    headers=headers,
                    timeout=30
                )
                
                if grocery_response.status_code == 200:
                    grocery_data = grocery_response.json()
                    
                    print_result("✅ Complete flow successful!", "success")
                    print_result(f"Recipe: {selected_recipe.get('title', 'Unknown')}", "info")
                    print_result(f"Total items: {grocery_data.get('total_items', 0)}", "info")
                    print_result(f"Kroger items found: {grocery_data.get('kroger_items_found', 0)}", "info")
                    print_result(f"Total cost: ${grocery_data.get('total_estimated_cost', 0)}", "info")
                    
                    # Show first few items with Kroger data
                    items = grocery_data.get("items", [])
                    print_result("Sample items with Kroger data:", "info")
                    for i, item in enumerate(items[:3], 1):
                        print_result(f"  {i}. {item.get('name', 'Unknown')}", "info")
                        print_result(f"     Price: ${item.get('estimated_price', 0)}", "info")
                        if item.get('product_id'):
                            print_result(f"     Kroger Product ID: {item['product_id']}", "success")
                        if item.get('brand'):
                            print_result(f"     Brand: {item['brand']}", "info")
                    
                    return True
                else:
                    print_result(f"❌ Grocery list creation failed: {grocery_response.status_code}", "error")
                    return False
            else:
                print_result("❌ No recipes generated", "error")
                return False
        else:
            print_result(f"❌ Recipe generation failed: {recipe_response.status_code}", "error")
            return False
            
    except Exception as e:
        print_result(f"❌ Flow test error: {e}", "error")
        return False

def main():
    """Run all comprehensive tests"""
    print("🛒 Comprehensive Kroger API Test Suite")
    print("=" * 60)
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Direct Kroger API", test_direct_kroger_api),
        ("Grocery Agent Functions", test_grocery_agent_functions),
        ("Grocery Endpoint", test_grocery_endpoint),
        ("Complete Recipe-to-Grocery Flow", test_complete_recipe_to_grocery_flow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print_result(f"✅ {test_name} PASSED", "success")
            else:
                print_result(f"❌ {test_name} FAILED", "error")
        except Exception as e:
            print_result(f"❌ {test_name} ERROR: {e}", "error")
    
    # Final summary
    print_separator("Final Test Summary")
    print_result(f"Tests passed: {passed}/{total}", "success" if passed == total else "warning")
    
    if passed == total:
        print_result("🎉 ALL TESTS PASSED! Kroger API integration is fully working!", "success")
    else:
        print_result("⚠️ Some tests failed. Check the output above for details.", "warning")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
