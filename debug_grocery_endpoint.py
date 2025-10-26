#!/usr/bin/env python3
"""
Debug script to test the search_and_price_ingredient function directly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_search_function():
    """Debug the search_and_price_ingredient function"""
    
    print("🔍 Debugging search_and_price_ingredient function")
    print("=" * 60)
    
    try:
        from agents.grocery_agent.agent import search_and_price_ingredient
        
        # Test with the same data as the endpoint
        test_cases = [
            ("paneer", 200, "g"),
            ("milk", 1, "gallon"),
            ("quinoa", 1, "cup"),
            ("ghee", 2, "tbsp"),
            ("garam masala", 1, "tsp")
        ]
        
        for ingredient_name, quantity, unit in test_cases:
            print(f"\n🧪 Testing: {ingredient_name} - {quantity} {unit}")
            
            result = search_and_price_ingredient(ingredient_name, quantity, unit)
            
            print(f"  Name: {result['name']}")
            print(f"  Price: ${result['price']}")
            print(f"  Source: {result['source']}")
            print(f"  Category: {result['category']}")
            print(f"  Brand: {result['brand']}")
            
            # Calculate what the total should be
            total_price = result['price'] * quantity
            print(f"  Expected total: ${result['price']} × {quantity} = ${total_price}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_search_function()
