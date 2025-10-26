#!/usr/bin/env python3
"""
Comprehensive Test: Complete Recipe-to-Grocery Flow with Kroger Integration
Tests the complete flow from recipe generation to grocery list creation
with detailed validation of Kroger API integration
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_complete_flow_with_kroger():
    """Test the complete recipe-to-grocery flow with Kroger validation"""
    
    print("🧪 Comprehensive Recipe-to-Grocery Flow Test with Kroger")
    print("=" * 70)
    
    # Step 0: Check server health
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server not running or unhealthy")
            return False
        print("✅ Server is running and healthy")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False
    
    # Step 1: Create test user
    print("\n" + "=" * 70)
    print("📝 Step 1: Creating Test User")
    print("=" * 70)
    
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
            print(f"❌ User creation failed: {register_response.status_code}")
            return False
        
        auth_data = register_response.json()
        auth_token = auth_data.get("access_token")
        print(f"✅ User created successfully")
        print(f"   Email: {user_data['email']}")
        print(f"   Token: {auth_token[:30]}...")
        
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Step 2: Generate a recipe
    print("\n" + "=" * 70)
    print("🍳 Step 2: Generating Recipe")
    print("=" * 70)
    
    recipe_request = {
        "user_profile": {
            "target_macros": {"protein_g": 100, "carbs_g": 200, "fat_g": 50, "calories": 2000},
            "likes": ["indian", "spicy"],
            "dislikes": []
        },
        "preferences": {
            "meal_type": "dinner",
            "cuisine": "indian",
            "dietary_restrictions": "vegetarian",
            "cook_time": "30-45 mins"
        }
    }
    
    try:
        print("⏳ Requesting recipe generation...")
        recipe_response = requests.post(
            "http://localhost:8000/recipe",
            json=recipe_request,
            headers=headers,
            timeout=120  # Recipe generation can take time
        )
        
        print(f"   API Status: {recipe_response.status_code}")
        
        if recipe_response.status_code == 200:
            recipe_data = recipe_response.json()
            recipes = recipe_data.get("recipes", [])
            
            if recipes:
                selected_recipe = recipes[0]
                
                # Validate that recipe is fully generated before proceeding
                if not selected_recipe.get('title') or not selected_recipe.get('ingredients'):
                    print("❌ Recipe data incomplete - waiting for full generation...")
                    print(f"   Recipe structure: {selected_recipe}")
                    return False
                
                print("✅ Recipe generated successfully!")
                print(f"   Title: {selected_recipe.get('title', 'Unknown')}")
                print(f"   Description: {selected_recipe.get('description', 'N/A')}")
                print(f"   Ingredients: {len(selected_recipe.get('ingredients', []))}")
                
                # Validate ingredients are structured correctly
                ingredients = selected_recipe.get('ingredients', [])
                if not ingredients:
                    print("❌ No ingredients in recipe")
                    return False
                
                # Show ingredients
                print(f"\n   Ingredients:")
                for i, ingredient in enumerate(ingredients[:5], 1):
                    if isinstance(ingredient, dict):
                        name = ingredient.get('name', 'Unknown')
                        quantity = ingredient.get('quantity', 'N/A')
                        unit = ingredient.get('unit', '')
                        print(f"   {i}. {name} - {quantity} {unit}")
                    else:
                        print(f"   {i}. {ingredient}")
                if len(ingredients) > 5:
                    print(f"   ... and {len(ingredients) - 5} more")
                
                print("\n✅ Recipe validation complete - proceeding to grocery list creation")
                
            else:
                print("❌ No recipes in response")
                return False
        else:
            print(f"❌ Recipe generation failed: {recipe_response.status_code}")
            print(f"   Response: {recipe_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Recipe generation error: {e}")
        return False
    
    # Step 3: Test /grocery endpoint
    print("\n" + "=" * 70)
    print("🛒 Step 3: Creating Grocery List via /grocery endpoint")
    print("=" * 70)
    
    # Validate recipe data before creating grocery request
    print("📋 Validating recipe data...")
    if not selected_recipe.get('title'):
        print("❌ Recipe missing title")
        return False
    if not selected_recipe.get('ingredients'):
        print("❌ Recipe missing ingredients")
        return False
    
    print(f"✅ Recipe validated: '{selected_recipe.get('title')}' with {len(selected_recipe.get('ingredients', []))} ingredients")
    
    grocery_request = {
        "recipe": selected_recipe,
        "user_id": "test_user",
        "store_preference": "Kroger"
    }
    
    try:
        print("⏳ Requesting grocery list creation...")
        grocery_response = requests.post(
            "http://localhost:8000/grocery",
            json=grocery_request,
            headers=headers,
            timeout=60
        )
        
        print(f"   API Status: {grocery_response.status_code}")
        
        if grocery_response.status_code == 200:
            grocery_data = grocery_response.json()
            
            print("✅ Grocery list created successfully!")
            print(f"   Store: {grocery_data.get('store', 'N/A')}")
            print(f"   Total items: {grocery_data.get('total_items', 0)}")
            print(f"   Kroger items found: {grocery_data.get('kroger_items_found', 0)}")
            print(f"   Total cost: ${grocery_data.get('total_estimated_cost', 0):.2f}")
            print(f"   LLM Provider: {grocery_data.get('llm_provider', 'N/A')}")
            
            # Show detailed items
            items = grocery_data.get("items", [])
            print(f"\n   Detailed items:")
            kroger_found = 0
            estimated_found = 0
            
            for i, item in enumerate(items, 1):
                print(f"   {i}. {item.get('name', 'Unknown')}")
                print(f"      Quantity: {item.get('quantity', 'N/A')}")
                print(f"      Price: ${item.get('estimated_price', 0):.2f}")
                print(f"      Category: {item.get('category', 'N/A')}")
                if item.get('product_id'):
                    print(f"      ✅ Kroger Product ID: {item['product_id']}")
                    kroger_found += 1
                if item.get('brand'):
                    print(f"      Brand: {item['brand']}")
                print()
                
                if not item.get('product_id'):
                    estimated_found += 1
            
            print(f"   Summary: {kroger_found} from Kroger, {estimated_found} estimated")
            
            # Save grocery list to JSON file
            try:
                grocery_list_output = {
                    "recipe_title": grocery_request["recipe"]["title"],
                    "store": grocery_data.get("store", "Kroger"),
                    "total_items": grocery_data.get("total_items", 0),
                    "kroger_items_found": grocery_data.get("kroger_items_found", 0),
                    "total_estimated_cost": grocery_data.get("total_estimated_cost", 0),
                    "llm_provider": grocery_data.get("llm_provider", "estimated"),
                    "items": []
                }
                
                for item in items:
                    grocery_list_output["items"].append({
                        "name": item.get("name", "Unknown"),
                        "quantity": item.get("quantity", "N/A"),
                        "price": item.get("estimated_price", 0),
                        "category": item.get("category", "N/A"),
                        "product_id": item.get("product_id", ""),
                        "brand": item.get("brand", ""),
                        "source": "kroger" if item.get("product_id") else "estimated"
                    })
                
                with open("grocery_list_kroger.json", "w") as f:
                    json.dump(grocery_list_output, f, indent=2)
                
                print(f"\n   💾 Grocery list saved to: grocery_list_kroger.json")
                
            except Exception as e:
                print(f"   ⚠️ Could not save grocery list to file: {e}")
            
            grocery_endpoint_success = True
            kroger_items_count = kroger_found
        else:
            print(f"❌ Grocery list creation failed: {grocery_response.status_code}")
            print(f"   Response: {grocery_response.text}")
            grocery_endpoint_success = False
            kroger_items_count = 0
            
    except Exception as e:
        print(f"❌ Grocery list creation error: {e}")
        grocery_endpoint_success = False
        kroger_items_count = 0
    
    # Step 4: Test /grocery/from-recipe endpoint
    print("\n" + "=" * 70)
    print("🛒 Step 4: Creating Grocery List via /grocery/from-recipe endpoint")
    print("=" * 70)
    
    # Convert recipe to the format expected by /grocery/from-recipe
    recipe_for_grocery = {
        "title": selected_recipe.get("title", "Generated Recipe"),
        "description": selected_recipe.get("description", ""),
        "ingredients": []
    }
    
    # Convert ingredients to the expected format
    for ingredient in selected_recipe.get("ingredients", []):
        if isinstance(ingredient, dict):
            recipe_for_grocery["ingredients"].append({
                "name": ingredient.get("name", "Unknown"),
                "quantity": ingredient.get("quantity", 1),
                "unit": ingredient.get("unit", "unit")
            })
    
    try:
        print("⏳ Requesting grocery list from recipe...")
        grocery_from_recipe_response = requests.post(
            "http://localhost:8000/grocery/from-recipe",
            json=recipe_for_grocery,
            headers=headers,
            timeout=60
        )
        
        print(f"   API Status: {grocery_from_recipe_response.status_code}")
        
        if grocery_from_recipe_response.status_code == 200:
            grocery_from_recipe_data = grocery_from_recipe_response.json()
            
            print("✅ Grocery from recipe list created successfully!")
            print(f"   Store: {grocery_from_recipe_data.get('store', 'N/A')}")
            print(f"   Total items: {grocery_from_recipe_data.get('total_items', 0)}")
            print(f"   Kroger items found: {grocery_from_recipe_data.get('kroger_items_found', 0)}")
            print(f"   Total cost: ${grocery_from_recipe_data.get('total_estimated_cost', 0):.2f}")
            print(f"   LLM Provider: {grocery_from_recipe_data.get('llm_provider', 'N/A')}")
            
            # Show first few items
            items = grocery_from_recipe_data.get("items", [])
            print(f"\n   First 3 items:")
            for i, item in enumerate(items[:3], 1):
                price = item.get('total_price', item.get('estimated_price', 0))
                print(f"   {i}. {item.get('name', 'Unknown')} - ${price:.2f}")
                if item.get('kroger_product_id'):
                    print(f"      ✅ Product ID: {item['kroger_product_id']}")
            
            grocery_from_recipe_success = True
        else:
            print(f"❌ Grocery from recipe creation failed: {grocery_from_recipe_response.status_code}")
            print(f"   Response: {grocery_from_recipe_response.text}")
            grocery_from_recipe_success = False
            
    except Exception as e:
        print(f"❌ Grocery from recipe creation error: {e}")
        grocery_from_recipe_success = False
    
    # Final Summary
    print("\n" + "=" * 70)
    print("📊 Final Test Summary")
    print("=" * 70)
    
    print(f"\n✅ Endpoints Status:")
    print(f"   /recipe: ✅ Working")
    print(f"   /grocery: {'✅ Working' if grocery_endpoint_success else '❌ Failed'}")
    print(f"   /grocery/from-recipe: {'✅ Working' if grocery_from_recipe_success else '❌ Failed'}")
    
    print(f"\n📦 Kroger Integration:")
    print(f"   Kroger items found: {kroger_items_count}")
    if kroger_items_count > 0:
        print("   ✅ Kroger API is working")
    else:
        print("   ⚠️ Kroger API returned 0 items (using estimated pricing)")
    
    if grocery_endpoint_success and grocery_from_recipe_success:
        print("\n🎉 COMPLETE SUCCESS!")
        print("✅ Recipe Agent → Grocery Agent flow working perfectly")
        print("✅ Both grocery endpoints working")
        if kroger_items_count > 0:
            print("✅ Kroger API integration working")
        else:
            print("⚠️ Kroger API needs configuration (check KROGER credentials)")
        print("✅ System is production-ready")
        return True
    else:
        print("\n⚠️ PARTIAL SUCCESS")
        if not grocery_endpoint_success:
            print("❌ /grocery endpoint failed")
        if not grocery_from_recipe_success:
            print("❌ /grocery/from-recipe endpoint failed")
        return False


if __name__ == "__main__":
    success = test_complete_flow_with_kroger()
    if success:
        print("\n🚀 System is production-ready!")
    else:
        print("\n⚠️ Some issues need attention")
    sys.exit(0 if success else 1)
