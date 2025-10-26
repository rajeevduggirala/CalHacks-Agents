#!/usr/bin/env python3
"""
Test script for improved Kroger API search functionality
Tests the enhanced search strategies for recipe ingredients
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_improved_search():
    """Test the improved Kroger API search with various ingredients"""
    
    print("🧪 Testing Improved Kroger API Search")
    print("=" * 50)
    
    # Test ingredients from recipe agent
    test_ingredients = [
        # Common grocery items
        "milk",
        "bread", 
        "chicken",
        "eggs",
        "cheese",
        
        # Indian/specialty ingredients
        "paneer",
        "quinoa",
        "ghee",
        "garam masala",
        "turmeric",
        "cumin",
        "chickpeas",
        "toor dal",
        
        # Produce
        "tomatoes",
        "onions",
        "bell peppers",
        "spinach"
    ]
    
    try:
        from agents.grocery_agent.agent import search_kroger_product, get_kroger_token
        
        # Test token first
        print("1. Testing token generation...")
        token = get_kroger_token()
        if not token:
            print("❌ Failed to get token")
            return False
        print(f"✅ Token obtained: {token[:20]}...")
        
        print("\n2. Testing improved product search...")
        print("-" * 50)
        
        found_count = 0
        total_tested = 0
        
        for ingredient in test_ingredients:
            total_tested += 1
            print(f"\n🔍 Searching for: {ingredient}")
            
            try:
                result = search_kroger_product(ingredient)
                
                if result and result.get("price"):
                    found_count += 1
                    print(f"✅ Found: {result['name']}")
                    print(f"   Price: ${result['price']}")
                    print(f"   Brand: {result.get('brand', 'N/A')}")
                    print(f"   Product ID: {result.get('product_id', 'N/A')}")
                    if result.get('size'):
                        print(f"   Size: {result['size']}")
                else:
                    print(f"⚠️ Not found or no price available")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Results: {found_count}/{total_tested} ingredients found")
        
        if found_count > 0:
            print("✅ Improved search is working!")
            return True
        else:
            print("⚠️ No products found - may need further tuning")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_search_strategies():
    """Test individual search strategies"""
    
    print("\n🧪 Testing Search Strategies")
    print("=" * 50)
    
    try:
        from agents.grocery_agent.agent import _get_search_strategies
        
        test_ingredients = ["paneer", "milk", "garam masala", "quinoa"]
        
        for ingredient in test_ingredients:
            print(f"\n🔍 Strategies for '{ingredient}':")
            strategies = _get_search_strategies(ingredient)
            
            for i, (strategy_name, params) in enumerate(strategies, 1):
                print(f"  {i}. {strategy_name}: {params}")
            
            print(f"  Total strategies: {len(strategies)}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🛒 Improved Kroger API Search Test")
    print("Based on: https://developer.kroger.com/documentation/api-products/public/products/overview")
    print()
    
    # Test search strategies
    test_search_strategies()
    
    # Test actual search
    success = test_improved_search()
    
    if success:
        print("\n🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Test completed with issues")
        sys.exit(1)
