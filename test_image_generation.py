#!/usr/bin/env python3
"""
Test Image Generation for Recipe Agent
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from agents.recipe_agent.agent import generate_recipe_image

def test_image_generation():
    """Test image URL generation"""
    
    print("=" * 80)
    print("Testing Recipe Image Generation")
    print("=" * 80)
    
    # Test cases
    test_recipes = [
        ("Spicy Paneer Tikka Masala", "Rich and creamy Indian curry with paneer"),
        ("Chocolate Chip Cookies", "Classic homemade cookies"),
        ("Caesar Salad", "Fresh romaine lettuce with dressing")
    ]
    
    for recipe_title, description in test_recipes:
        print(f"\n📝 Recipe: {recipe_title}")
        print(f"   Description: {description}")
        
        image_url = generate_recipe_image(recipe_title, description)
        
        print(f"   Image URL: {image_url}")
        print(f"   URL length: {len(image_url)} characters")
        
        # Check if URL starts with expected prefix
        if "pollinations.ai" in image_url:
            print("   ✅ Using Pollinations.ai image generation")
        elif "placeholder.com" in image_url:
            print("   ⚠️  Using fallback placeholder image")
        else:
            print("   ❓ Unknown image service")
    
    print("\n" + "=" * 80)
    print("Image Generation Test Complete")
    print("=" * 80)
    
    # Test one image URL to verify it's accessible
    print("\n🔍 Testing image URL accessibility...")
    test_url = generate_recipe_image("Test Recipe", "A test dish")
    print(f"Test URL: {test_url}")
    
    try:
        response = requests.head(test_url, timeout=10, allow_redirects=True)
        print(f"HTTP Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Image URL is accessible")
        else:
            print(f"⚠️  Image URL returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing image URL: {e}")

if __name__ == "__main__":
    test_image_generation()
