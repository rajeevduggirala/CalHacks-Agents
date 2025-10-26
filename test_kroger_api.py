#!/usr/bin/env python3
"""
Kroger API Test Script
Tests the Kroger API integration for grocery list generation
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

from agents.grocery_agent.agent import (
    get_kroger_token, 
    search_kroger_product, 
    search_and_price_ingredient,
    create_grocery_list
)

class KrogerAPITester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.auth_token = None
        self.test_results = {
            "token_test": False,
            "product_search": False,
            "grocery_endpoint": False,
            "recipe_to_grocery": False
        }
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str, status: str = "info"):
        """Print a formatted step"""
        icons = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        print(f"{icons.get(status, 'ℹ️')} {step}")
    
    def test_environment_setup(self):
        """Test if Kroger API credentials are configured"""
        self.print_header("Environment Setup Check")
        
        client_id = os.getenv("KROGER_CLIENT_ID")
        client_secret = os.getenv("KROGER_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            self.print_step("❌ Kroger API credentials not found in environment", "error")
            self.print_step("Please set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET in your .env file", "warning")
            return False
        
        if client_id == "your_kroger_client_id_here":
            self.print_step("❌ Default placeholder credentials detected", "error")
            self.print_step("Please update .env with real Kroger API credentials", "warning")
            return False
        
        self.print_step(f"✅ KROGER_CLIENT_ID: {client_id[:10]}...", "success")
        self.print_step(f"✅ KROGER_CLIENT_SECRET: {'*' * len(client_secret)}", "success")
        return True
    
    def test_kroger_token(self):
        """Test Kroger API token generation"""
        self.print_header("Kroger API Token Test")
        
        try:
            token = get_kroger_token()
            if token:
                self.print_step("✅ Successfully obtained Kroger API token", "success")
                self.print_step(f"Token: {token[:20]}...", "info")
                self.test_results["token_test"] = True
                return True
            else:
                self.print_step("❌ Failed to obtain Kroger API token", "error")
                return False
        except Exception as e:
            self.print_step(f"❌ Error getting token: {e}", "error")
            return False
    
    def test_product_search(self):
        """Test individual product search"""
        self.print_header("Product Search Test")
        
        test_products = [
            "milk",
            "bread", 
            "chicken",
            "tomatoes",
            "paneer",  # Indian ingredient
            "quinoa"
        ]
        
        success_count = 0
        
        for product in test_products:
            try:
                result = search_kroger_product(product)
                if result and result.get("price"):
                    self.print_step(f"✅ Found '{product}': ${result['price']} (ID: {result.get('product_id', 'N/A')})", "success")
                    success_count += 1
                else:
                    self.print_step(f"⚠️ '{product}' not found or no price available", "warning")
            except Exception as e:
                self.print_step(f"❌ Error searching '{product}': {e}", "error")
        
        if success_count > 0:
            self.print_step(f"✅ Found {success_count}/{len(test_products)} products", "success")
            self.test_results["product_search"] = True
            return True
        else:
            self.print_step("❌ No products found", "error")
            return False
    
    def test_ingredient_pricing(self):
        """Test ingredient pricing with fallback"""
        self.print_header("Ingredient Pricing Test")
        
        test_ingredients = [
            ("paneer", 200, "g"),
            ("quinoa", 1, "cup"),
            ("tomatoes", 2, "whole"),
            ("chicken", 500, "g"),
            ("nonexistent_item", 1, "unit")  # Test fallback
        ]
        
        kroger_found = 0
        fallback_used = 0
        
        for name, qty, unit in test_ingredients:
            try:
                result = search_and_price_ingredient(name, qty, unit)
                source = result.get("source", "unknown")
                
                if source == "kroger_api":
                    self.print_step(f"✅ {name}: ${result['price']} (Kroger API)", "success")
                    kroger_found += 1
                elif source == "estimated":
                    self.print_step(f"⚠️ {name}: ${result['price']} (estimated)", "warning")
                    fallback_used += 1
                else:
                    self.print_step(f"❌ {name}: Unknown source", "error")
                    
            except Exception as e:
                self.print_step(f"❌ Error pricing '{name}': {e}", "error")
        
        self.print_step(f"📊 Results: {kroger_found} from Kroger, {fallback_used} estimated", "info")
        return kroger_found > 0 or fallback_used > 0
    
    def create_test_user(self):
        """Create a test user for API testing"""
        self.print_header("Creating Test User")
        
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
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.print_step("✅ Test user created successfully", "success")
                return True
            else:
                self.print_step(f"❌ User creation failed: {response.status_code}", "error")
                self.print_step(f"Response: {response.text}", "error")
                return False
                
        except Exception as e:
            self.print_step(f"❌ User creation error: {e}", "error")
            return False
    
    def test_grocery_endpoint(self):
        """Test the grocery endpoint with a sample recipe"""
        self.print_header("Grocery Endpoint Test")
        
        if not self.auth_token:
            self.print_step("❌ No auth token available", "error")
            return False
        
        # Sample recipe for testing
        test_recipe = {
            "title": "Test Paneer Curry",
            "description": "A test recipe for Kroger API",
            "ingredients": [
                {"name": "paneer", "quantity": 200, "unit": "g", "notes": "cubed"},
                {"name": "tomatoes", "quantity": 2, "unit": "whole", "notes": "chopped"},
                {"name": "onions", "quantity": 1, "unit": "medium", "notes": "diced"},
                {"name": "garam masala", "quantity": 1, "unit": "tsp", "notes": None},
                {"name": "milk", "quantity": 1, "unit": "cup", "notes": None}
            ]
        }
        
        grocery_request = {
            "recipe": test_recipe,
            "user_id": "test_user",
            "store_preference": "Kroger"
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(
                f"{self.base_url}/grocery",
                json=grocery_request,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                kroger_found = data.get("kroger_items_found", 0)
                total_cost = data.get("total_estimated_cost", 0)
                
                self.print_step(f"✅ Grocery list created successfully", "success")
                self.print_step(f"📦 Items: {len(items)}", "info")
                self.print_step(f"🛒 Kroger items found: {kroger_found}", "info")
                self.print_step(f"💰 Total cost: ${total_cost}", "info")
                
                # Show first few items
                for i, item in enumerate(items[:3], 1):
                    name = item.get("name", "Unknown")
                    price = item.get("estimated_price", 0)
                    product_id = item.get("product_id", "N/A")
                    self.print_step(f"  {i}. {name}: ${price} (ID: {product_id})", "info")
                
                self.test_results["grocery_endpoint"] = True
                return True
            else:
                self.print_step(f"❌ Grocery endpoint failed: {response.status_code}", "error")
                self.print_step(f"Response: {response.text}", "error")
                return False
                
        except Exception as e:
            self.print_step(f"❌ Grocery endpoint error: {e}", "error")
            return False
    
    def test_recipe_to_grocery_flow(self):
        """Test the complete flow: recipe generation -> grocery list"""
        self.print_header("Complete Recipe-to-Grocery Flow Test")
        
        if not self.auth_token:
            self.print_step("❌ No auth token available", "error")
            return False
        
        # Step 1: Generate a recipe
        self.print_step("Step 1: Generating recipe...", "info")
        
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
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(
                f"{self.base_url}/recipe",
                json=recipe_request,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                recipe_data = response.json()
                recipes = recipe_data.get("recipes", [])
                
                if recipes:
                    # Use the first recipe
                    selected_recipe = recipes[0]
                    self.print_step(f"✅ Generated recipe: {selected_recipe.get('title', 'Unknown')}", "success")
                    
                    # Step 2: Create grocery list from recipe
                    self.print_step("Step 2: Creating grocery list...", "info")
                    
                    grocery_request = {
                        "recipe": selected_recipe,
                        "user_id": "test_user",
                        "store_preference": "Kroger"
                    }
                    
                    grocery_response = requests.post(
                        f"{self.base_url}/grocery",
                        json=grocery_request,
                        headers=headers,
                        timeout=30
                    )
                    
                    if grocery_response.status_code == 200:
                        grocery_data = grocery_response.json()
                        kroger_found = grocery_data.get("kroger_items_found", 0)
                        total_items = grocery_data.get("total_items", 0)
                        total_cost = grocery_data.get("total_estimated_cost", 0)
                        
                        self.print_step(f"✅ Complete flow successful!", "success")
                        self.print_step(f"📊 Kroger items: {kroger_found}/{total_items}", "info")
                        self.print_step(f"💰 Total cost: ${total_cost}", "info")
                        
                        self.test_results["recipe_to_grocery"] = True
                        return True
                    else:
                        self.print_step(f"❌ Grocery list creation failed: {grocery_response.status_code}", "error")
                        return False
                else:
                    self.print_step("❌ No recipes generated", "error")
                    return False
            else:
                self.print_step(f"❌ Recipe generation failed: {response.status_code}", "error")
                return False
                
        except Exception as e:
            self.print_step(f"❌ Flow test error: {e}", "error")
            return False
    
    def run_all_tests(self):
        """Run all Kroger API tests"""
        self.print_header("Kroger API Comprehensive Test Suite")
        
        print("🧪 Testing Kroger API integration for Agentic Grocery")
        print("📅 Test started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Test sequence
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Kroger Token", self.test_kroger_token),
            ("Product Search", self.test_product_search),
            ("Ingredient Pricing", self.test_ingredient_pricing),
            ("Test User Creation", self.create_test_user),
            ("Grocery Endpoint", self.test_grocery_endpoint),
            ("Recipe-to-Grocery Flow", self.test_recipe_to_grocery_flow)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.print_step(f"❌ {test_name} failed with exception: {e}", "error")
        
        # Summary
        self.print_header("Test Summary")
        self.print_step(f"📊 Tests passed: {passed}/{total}", "success" if passed == total else "warning")
        
        if passed == total:
            self.print_step("🎉 All tests passed! Kroger API integration is working correctly.", "success")
        else:
            self.print_step("⚠️ Some tests failed. Check the output above for details.", "warning")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name.replace('_', ' ').title()}")
        
        return passed == total


def main():
    """Main test runner"""
    print("🛒 Kroger API Test Script for Agentic Grocery")
    print("=" * 60)
    
    tester = KrogerAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
