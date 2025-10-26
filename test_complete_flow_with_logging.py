#!/usr/bin/env python3
"""
Complete End-to-End Test with Comprehensive Logging
Tests: Registration → Recipe Generation → Grocery List Creation
All output saved to log file
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Generate timestamped log file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_path = f"logs/test_flow_{timestamp}.log"

# Create a custom print function that writes to both console and file
class TeeOutput:
    def __init__(self, *files):
        self.files = files
    
    def write(self, text):
        for f in self.files:
            f.write(text)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()

# Open log file
log_file = open(log_file_path, 'w', encoding='utf-8')
original_stdout = sys.stdout

# Redirect stdout to both console and file
sys.stdout = TeeOutput(original_stdout, log_file)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_info(message):
    """Print an info message"""
    print(f"ℹ️  {message}")

def print_success(message):
    """Print a success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message"""
    print(f"❌ {message}")

def test_complete_flow():
    """Test the complete flow: Register → Generate Recipe → Create Grocery List"""
    
    print_section("Agentic Grocery - Complete Flow Test")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log file: {log_file_path}\n")
    
    # Step 0: Check server health
    print_section("Step 0: Server Health Check")
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            print_success("Server is running and healthy")
            print(json.dumps(health_response.json(), indent=2))
        else:
            print_error(f"Server health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print_error(f"Server not accessible: {e}")
        return False
    
    # Step 1: Register User
    print_section("Step 1: User Registration")
    
    timestamp = int(datetime.now().timestamp())
    user_data = {
        "email": f"testuser{timestamp}@example.com",
        "username": f"testuser{timestamp}",
        "password": "TestPass123!",
        "name": "Test User",
        "daily_calories": 2200,
        "dietary_restrictions": ["vegetarian"],
        "likes": ["indian", "spicy", "mediterranean"],
        "additional_information": "Love bold flavors and spices"
    }
    
    print_info(f"Registering user: {user_data['email']}")
    print(json.dumps(user_data, indent=2))
    
    try:
        register_response = requests.post(
            "http://localhost:8000/auth/register",
            json=user_data,
            timeout=10
        )
        
        print(f"\nResponse Status: {register_response.status_code}")
        
        if register_response.status_code in [200, 201]:
            auth_data = register_response.json()
            auth_token = auth_data.get("access_token")
            
            print_success("User registered successfully!")
            print(f"Token: {auth_token[:50]}...")
            print("\nFull Response:")
            print(json.dumps(auth_data, indent=2))
        else:
            print_error(f"Registration failed: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            return False
            
    except Exception as e:
        print_error(f"Registration error: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Step 2: Generate Recipes
    print_section("Step 2: Recipe Generation")
    
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
    
    print_info("Requesting recipe generation...")
    print(json.dumps(recipe_request, indent=2))
    
    try:
        recipe_response = requests.post(
            "http://localhost:8000/recipe",
            json=recipe_request,
            headers=headers,
            timeout=120
        )
        
        print(f"\nResponse Status: {recipe_response.status_code}")
        
        if recipe_response.status_code == 200:
            recipe_data = recipe_response.json()
            recipes = recipe_data.get("recipes", [])
            
            if recipes:
                selected_recipe = recipes[0]
                
                print_success("Recipe generated successfully!")
                print(f"\nSelected Recipe: {selected_recipe.get('title')}")
                print(f"Description: {selected_recipe.get('description')}")
                print(f"Ingredients: {len(selected_recipe.get('ingredients', []))}")
                
                print("\nFull Recipe Data:")
                print(json.dumps(selected_recipe, indent=2))
                
            else:
                print_error("No recipes in response")
                return False
        else:
            print_error(f"Recipe generation failed: {recipe_response.status_code}")
            print(f"Response: {recipe_response.text}")
            return False
            
    except Exception as e:
        print_error(f"Recipe generation error: {e}")
        return False
    
    # Step 3: Create Grocery List
    print_section("Step 3: Grocery List Creation")
    
    grocery_request = {
        "recipe": selected_recipe,
        "user_id": "test_user",
        "store_preference": "Kroger"
    }
    
    print_info("Creating grocery list from recipe...")
    print(f"Recipe: {selected_recipe.get('title')}")
    print(f"Ingredients to search: {len(selected_recipe.get('ingredients', []))}")
    
    try:
        grocery_response = requests.post(
            "http://localhost:8000/grocery",
            json=grocery_request,
            headers=headers,
            timeout=60
        )
        
        print(f"\nResponse Status: {grocery_response.status_code}")
        
        if grocery_response.status_code == 200:
            grocery_data = grocery_response.json()
            
            print_success("Grocery list created successfully!")
            print(f"Store: {grocery_data.get('store')}")
            print(f"Total items: {grocery_data.get('total_items')}")
            print(f"Kroger items found: {grocery_data.get('kroger_items_found')}")
            print(f"Total cost: ${grocery_data.get('total_estimated_cost', 0):.2f}")
            
            print("\nDetailed Items:")
            items = grocery_data.get("items", [])
            for i, item in enumerate(items, 1):
                print(f"\n  {i}. {item.get('name', 'Unknown')}")
                print(f"     Quantity: {item.get('quantity', 'N/A')}")
                print(f"     Price: ${item.get('estimated_price', 0):.2f}")
                print(f"     Category: {item.get('category', 'N/A')}")
                if item.get('product_id'):
                    print(f"     Product ID: {item['product_id']}")
                if item.get('brand'):
                    print(f"     Brand: {item['brand']}")
            
            print("\n\nFull Grocery List Response:")
            print(json.dumps(grocery_data, indent=2))
            
            # Save grocery list to JSON file
            grocery_json_file = f"logs/grocery_list_{timestamp}.json"
            with open(grocery_json_file, 'w') as f:
                json.dump(grocery_data, f, indent=2)
            print(f"\n💾 Grocery list saved to: {grocery_json_file}")
            
        else:
            print_error(f"Grocery list creation failed: {grocery_response.status_code}")
            print(f"Response: {grocery_response.text}")
            return False
            
    except Exception as e:
        print_error(f"Grocery list creation error: {e}")
        return False
    
    # Final Summary
    print_section("Test Summary")
    
    print_success("COMPLETE FLOW TEST PASSED!")
    print(f"\nUser: {user_data['email']}")
    print(f"Recipe: {selected_recipe.get('title')}")
    print(f"Grocery items: {grocery_data.get('total_items')} items")
    print(f"Kroger items: {grocery_data.get('kroger_items_found')} items")
    print(f"Total cost: ${grocery_data.get('total_estimated_cost', 0):.2f}")
    print(f"\nLog file: {log_file_path}")
    print(f"Grocery JSON: logs/grocery_list_{timestamp}.json")
    
    return True


if __name__ == "__main__":
    try:
        success = test_complete_flow()
        
        print("\n" + "=" * 80)
        if success:
            print("✅ TEST COMPLETED SUCCESSFULLY")
        else:
            print("❌ TEST FAILED")
        print("=" * 80)
        
    finally:
        # Restore stdout and close log file
        sys.stdout = original_stdout
        log_file.close()
        print(f"\n📄 Full log saved to: {log_file_path}")
