#!/usr/bin/env python3
"""Test Kroger API directly"""
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

def test_kroger_api():
    # Get credentials
    client_id = os.getenv('KROGER_CLIENT_ID')
    secret = os.getenv('KROGER_CLIENT_SECRET')
    location_id = os.getenv('KROGER_LOCATION_ID', '01400441')
    
    print(f"Client ID: {client_id[:20]}..." if client_id else "None")
    
    # Get token
    auth_string = f"{client_id}:{secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_base64}"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "product.compact"
    }
    
    print("\n1. Getting OAuth token...")
    r = requests.post('https://api.kroger.com/v1/connect/oauth2/token', headers=headers, data=data, timeout=10)
    print(f"Status: {r.status_code}")
    
    if r.status_code != 200:
        print(f"Error: {r.text}")
        return
    
    token = r.json()['access_token']
    print(f"Token: {token[:50]}...")
    
    # Test searches
    test_items = ['quinoa', 'tomatoes', 'paneer', 'greek yogurt', 'paneer cheese']
    
    headers2 = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    print("\n2. Testing product searches...")
    for item in test_items:
        print(f"\nSearching for: {item}")
        params = {
            "filter.locationId": location_id,
            "filter.term": item,
            "filter.limit": 3
        }
        
        r2 = requests.get('https://api.kroger.com/v1/products', headers=headers2, params=params, timeout=10)
        print(f"  Status: {r2.status_code}")
        
        if r2.status_code == 200:
            data = r2.json()
            products = data.get('data', [])
            print(f"  Found: {len(products)} products")
            
            if products:
                p = products[0]
                print(f"  First result: {p.get('description', 'N/A')}")
                
                # Try to get price
                items = p.get('items', [])
                if items and items[0].get('price'):
                    price_data = items[0]['price']
                    price = price_data.get('regular', price_data.get('promo'))
                    print(f"  Price: ${price}")
                    print(f"  Product ID: {p.get('productId', 'N/A')}")
                else:
                    print("  No price available")
        else:
            print(f"  Error: {r2.text[:200]}")

if __name__ == "__main__":
    test_kroger_api()
