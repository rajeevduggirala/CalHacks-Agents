#!/usr/bin/env python3
"""
Debug Recipe Agent - Test single day generation
"""

import requests
import json

def test_single_day():
    """Test generating meals for a single day"""
    base_url = "http://localhost:8000"
    
    # First, create a user
    print("🧪 Creating test user...")
    import time
    timestamp = int(time.time())
    user_data = {
        "email": f"debug{timestamp}@example.com",
        "username": f"debuguser{timestamp}",
        "password": "password123",
        "name": "Debug User",
        "daily_calories": 2000,
        "dietary_restrictions": ["vegetarian"],
        "likes": ["spicy"]
    }
    
    response = requests.post(f"{base_url}/auth/register", json=user_data)
    print(f"Registration status: {response.status_code}")
    
    if response.status_code not in [200, 201]:
        print(f"Registration failed: {response.text}")
        return
    
    # Get auth token
    auth_token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test the new endpoint
    print("\n🧪 Testing daily meals generation...")
    response = requests.post(
        f"{base_url}/daily-meals/generate-by-day?day=Monday",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_single_day()
