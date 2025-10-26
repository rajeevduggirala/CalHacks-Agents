#!/usr/bin/env python3
"""
Minimal registration test to isolate the issue
"""

import requests
import json

def test_minimal_registration():
    """Test with minimal required fields"""
    url = "http://localhost:8000/auth/register"
    
    # Minimal data with only required fields
    data = {
        "email": "minimal@example.com",
        "username": "minimaluser",
        "password": "password123",
        "name": "Minimal User",
        "daily_calories": 2000,
        "dietary_restrictions": ["vegetarian"],
        "likes": ["spicy"]
    }
    
    print("🧪 Testing minimal registration...")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Registration successful!")
            return True
        else:
            print("❌ Registration failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_minimal_registration()
