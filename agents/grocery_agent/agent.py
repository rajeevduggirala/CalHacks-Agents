"""
GroceryAgent - Grocery List Builder for Agentic Grocery
Extracts ingredients from selected recipes and creates formatted grocery lists.
Integrates with Kroger API for real product search and pricing.
ASI:One compatible with Chat Protocol v0.3.0

Agent Metadata:
- Name: GroceryAgent
- Description: Automated grocery list builder that extracts ingredients from recipes 
               and uses Kroger API for real product pricing and availability
- Tags: grocery, shopping, kroger, fetchai, agentic-ai, automation
- Endpoint: http://localhost:8000/grocery
- Version: 0.3.0
- Protocol: chat-protocol-v0.3.0
"""

import os
import json
from typing import Dict, Any, List, Optional
from uagents import Agent, Context, Model
from pydantic import BaseModel, Field
import sys
import requests
import base64
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.logger import setup_logger, log_agent_message


# Pydantic models for structured communication
class GroceryRequest(BaseModel):
    """Grocery list generation request"""
    recipe: Dict[str, Any] = Field(..., description="Selected recipe with ingredients")
    user_id: str = Field(default="raj", description="User identifier")
    store_preference: str = Field(default="Kroger", description="Preferred grocery store (Kroger API supported)")


class GroceryItem(BaseModel):
    """Individual grocery item"""
    name: str = Field(..., description="Item name")
    quantity: str = Field(..., description="Quantity needed")
    category: Optional[str] = Field(default=None, description="Item category")
    estimated_price: Optional[float] = Field(default=None, description="Estimated price in USD")


class GroceryResponse(BaseModel):
    """Grocery list response"""
    agent: str = Field(default="GroceryAgent", description="Agent name")
    store: str = Field(..., description="Store name")
    items: List[GroceryItem] = Field(..., description="List of grocery items")
    total_estimated_cost: float = Field(..., description="Total estimated cost")
    message: str = Field(..., description="Response message")
    order_url: Optional[str] = Field(default=None, description="Mock order URL")
    next_action: Optional[str] = Field(default="review_order", description="Next action")


# Initialize GroceryAgent
GROCERY_AGENT_SEED = os.getenv("GROCERY_AGENT_SEED", "grocery-agent-seed-11111")
grocery_agent = Agent(
    name="GroceryAgent",
    seed=GROCERY_AGENT_SEED,
    port=8003,
    endpoint=["http://localhost:8003/submit"]
)

logger = setup_logger("GroceryAgent")

# Kroger API configuration
KROGER_CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
KROGER_CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")
KROGER_API_BASE = os.getenv("KROGER_API_BASE", "https://api.kroger.com/v1")
_kroger_token = None
_token_expiry = None


# Mock price database for common ingredients
INGREDIENT_PRICES = {
    "paneer": 4.99,
    "cottage cheese": 4.99,
    "quinoa": 3.49,
    "yogurt": 2.99,
    "garam masala": 3.99,
    "turmeric": 2.49,
    "bell peppers": 2.99,
    "onions": 1.49,
    "chickpeas": 1.99,
    "sweet potato": 1.99,
    "spinach": 2.49,
    "tahini": 5.99,
    "cumin": 2.99,
    "chili powder": 2.49,
    "brown rice": 2.99,
    "toor dal": 3.49,
    "split pigeon peas": 3.49,
    "whole wheat flour": 2.99,
    "tomatoes": 2.49,
    "cumin seeds": 2.99,
    "ghee": 6.99,
    "ginger-garlic paste": 3.49,
    "green chilies": 1.99
}

CATEGORY_MAP = {
    "paneer": "Dairy",
    "cottage cheese": "Dairy",
    "yogurt": "Dairy",
    "quinoa": "Grains",
    "brown rice": "Grains",
    "whole wheat flour": "Grains",
    "bell peppers": "Produce",
    "onions": "Produce",
    "sweet potato": "Produce",
    "spinach": "Produce",
    "tomatoes": "Produce",
    "green chilies": "Produce",
    "chickpeas": "Canned Goods",
    "toor dal": "Grains & Beans",
    "split pigeon peas": "Grains & Beans",
    "tahini": "Condiments",
    "ginger-garlic paste": "Condiments",
    "garam masala": "Spices",
    "turmeric": "Spices",
    "cumin": "Spices",
    "cumin seeds": "Spices",
    "chili powder": "Spices",
    "ghee": "Cooking Oils"
}


def categorize_ingredient(ingredient_name: str) -> str:
    """Categorize ingredient for better organization"""
    ingredient_lower = ingredient_name.lower()
    
    # Try exact match first
    if ingredient_lower in CATEGORY_MAP:
        return CATEGORY_MAP[ingredient_lower]
    
    # Try partial match
    for key, category in CATEGORY_MAP.items():
        if key in ingredient_lower:
            return category
    
    return "Other"


def get_kroger_token() -> Optional[str]:
    """
    Get Kroger API OAuth token. Caches token until expiry.
    Returns None if credentials are not configured.
    """
    global _kroger_token, _token_expiry
    
    # Check if we have valid credentials
    if not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET:
        return None
    
    if KROGER_CLIENT_ID == "your_kroger_client_id_here":
        return None
    
    # Return cached token if still valid
    if _kroger_token and _token_expiry and datetime.now() < _token_expiry:
        return _kroger_token
    
    try:
        # Request new token
        auth_string = f"{KROGER_CLIENT_ID}:{KROGER_CLIENT_SECRET}"
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
        
        response = requests.post(
            f"{KROGER_API_BASE.replace('/v1', '')}/connect/oauth2/token",
            headers=headers,
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            _kroger_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 1800)  # Default 30 minutes
            _token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 min early
            
            log_agent_message("GroceryAgent", "✅ Kroger API token obtained")
            return _kroger_token
        else:
            logger.warning(f"Kroger API token request failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.warning(f"Error getting Kroger token: {e}")
        return None


def search_kroger_product(ingredient_name: str) -> Optional[Dict[str, Any]]:
    """
    Search for a product in Kroger's catalog.
    Returns product data with price if found.
    """
    token = get_kroger_token()
    if not token:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        # Search for product
        params = {
            "filter.term": ingredient_name,
            "filter.limit": 1
        }
        
        response = requests.get(
            f"{KROGER_API_BASE}/products",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", [])
            
            if products:
                product = products[0]
                # Extract price from items
                items = product.get("items", [])
                price = None
                
                if items and items[0].get("price"):
                    price_data = items[0]["price"]
                    price = price_data.get("regular", price_data.get("promo"))
                
                return {
                    "name": product.get("description", ingredient_name),
                    "price": price,
                    "product_id": product.get("productId"),
                    "upc": product.get("upc"),
                    "brand": product.get("brand")
                }
        
        return None
        
    except Exception as e:
        logger.debug(f"Kroger product search error for '{ingredient_name}': {e}")
        return None


def estimate_price(ingredient_name: str, quantity: str) -> float:
    """
    Estimate price for an ingredient.
    First tries Kroger API, then falls back to mock prices.
    """
    # Try Kroger API first
    kroger_product = search_kroger_product(ingredient_name)
    if kroger_product and kroger_product.get("price"):
        log_agent_message("GroceryAgent", f"📦 Found '{ingredient_name}' on Kroger: ${kroger_product['price']}")
        return float(kroger_product["price"])
    
    # Fallback to mock prices
    ingredient_lower = ingredient_name.lower()
    
    # Try exact match
    if ingredient_lower in INGREDIENT_PRICES:
        return INGREDIENT_PRICES[ingredient_lower]
    
    # Try partial match
    for key, price in INGREDIENT_PRICES.items():
        if key in ingredient_lower:
            return price
    
    # Default estimate
    return 3.99


def create_grocery_list(recipe: Dict[str, Any], store: str = "Kroger") -> Dict[str, Any]:
    """
    Create a grocery list from recipe ingredients.
    
    Args:
        recipe: Recipe dictionary with ingredients
        store: Preferred store name
    
    Returns:
        Grocery list with items and estimated costs
    """
    ingredients = recipe.get("ingredients", [])
    
    grocery_items = []
    total_cost = 0.0
    
    for ingredient in ingredients:
        item_name = ingredient.get("name", "Unknown")
        quantity = ingredient.get("quantity", "1")
        
        category = categorize_ingredient(item_name)
        price = estimate_price(item_name, quantity)
        
        grocery_item = GroceryItem(
            name=item_name,
            quantity=quantity,
            category=category,
            estimated_price=price
        )
        
        grocery_items.append(grocery_item)
        total_cost += price
    
    return {
        "store": store,
        "items": grocery_items,
        "total_estimated_cost": round(total_cost, 2)
    }


@grocery_agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup handler"""
    log_agent_message("GroceryAgent", "🚀 GroceryAgent started and ready!")
    logger.info(f"Agent address: {ctx.agent.address}")


@grocery_agent.on_message(model=GroceryRequest)
async def handle_grocery_request(ctx: Context, sender: str, msg: GroceryRequest):
    """
    Main message handler for GroceryAgent.
    Compatible with ASI:One Chat Protocol v0.3.0
    """
    log_agent_message("GroceryAgent", "📨 Received grocery list request")
    
    try:
        # Create grocery list
        grocery_data = create_grocery_list(msg.recipe, msg.store_preference)
        
        # Generate Kroger or store-specific order URL
        recipe_title = msg.recipe.get("title", "recipe").replace(" ", "-").lower()
        if msg.store_preference.lower() == "kroger":
            order_url = f"https://www.kroger.com/cart?recipe={recipe_title}"
        else:
            order_url = f"https://instacart.com/order/{msg.user_id}/{recipe_title}"
        
        response = GroceryResponse(
            store=grocery_data["store"],
            items=grocery_data["items"],
            total_estimated_cost=grocery_data["total_estimated_cost"],
            message=f"Created grocery list with {len(grocery_data['items'])} items. Total: ${grocery_data['total_estimated_cost']}",
            order_url=order_url,
            next_action="review_order"
        )
        
        log_agent_message("GroceryAgent", f"✅ Created list with {len(grocery_data['items'])} items")
        
        # Send response back
        await ctx.send(sender, response)
        
    except Exception as e:
        logger.error(f"Error creating grocery list: {e}")
        error_response = GroceryResponse(
            store="Instacart",
            items=[],
            total_estimated_cost=0.0,
            message=f"Sorry, I encountered an error: {str(e)}",
            next_action="retry"
        )
        await ctx.send(sender, error_response)


def generate_grocery_list(grocery_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper for grocery list generation.
    Used by FastAPI endpoints.
    """
    request = GroceryRequest(**grocery_request)
    grocery_data = create_grocery_list(request.recipe, request.store_preference)
    
    # Generate store-specific order URL
    recipe_title = request.recipe.get("title", "recipe").replace(" ", "-").lower()
    if request.store_preference.lower() == "kroger":
        order_url = f"https://www.kroger.com/cart?recipe={recipe_title}"
    else:
        order_url = f"https://instacart.com/order/{request.user_id}/{recipe_title}"
    
    return {
        "agent": "GroceryAgent",
        "store": grocery_data["store"],
        "items": [item.model_dump() for item in grocery_data["items"]],
        "total_estimated_cost": grocery_data["total_estimated_cost"],
        "message": f"Created grocery list with {len(grocery_data['items'])} items. Total: ${grocery_data['total_estimated_cost']}",
        "order_url": order_url,
        "next_action": "review_order"
    }


if __name__ == "__main__":
    log_agent_message("GroceryAgent", "Starting GroceryAgent...")
    grocery_agent.run()

