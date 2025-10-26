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
from typing import Dict, Any, List, Optional, Tuple
from uagents import Agent, Context, Model, Protocol
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
    """Individual grocery item with Kroger details"""
    name: str = Field(..., description="Item name")
    quantity: str = Field(..., description="Quantity needed")
    category: Optional[str] = Field(default=None, description="Item category")
    estimated_price: Optional[float] = Field(default=None, description="Price in USD (real or estimated)")
    product_id: Optional[str] = Field(default=None, description="Kroger product ID")
    upc: Optional[str] = Field(default=None, description="Universal Product Code")
    brand: Optional[str] = Field(default=None, description="Product brand")


class GroceryResponse(BaseModel):
    """Grocery list response with Kroger data"""
    agent: str = Field(default="GroceryAgent", description="Agent name")
    store: str = Field(..., description="Store name")
    items: List[GroceryItem] = Field(..., description="List of grocery items with Kroger details")
    total_estimated_cost: float = Field(..., description="Total cost (real or estimated)")
    kroger_items_found: int = Field(default=0, description="Number of items found on Kroger")
    total_items: int = Field(..., description="Total number of items")
    message: str = Field(..., description="Response message")
    order_url: Optional[str] = Field(default=None, description="Kroger order URL")
    next_action: Optional[str] = Field(default="review_order", description="Next action")
    tools_called: Optional[List[str]] = Field(default=None, description="List of tools/functions called")
    llm_provider: Optional[str] = Field(default="kroger_api", description="Data source used")


# Initialize GroceryAgent
GROCERY_AGENT_SEED = os.getenv("GROCERY_AGENT_SEED", "grocery-agent-seed-11111")
grocery_agent = Agent(
    name="GroceryAgent",
    seed=GROCERY_AGENT_SEED,
    port=8003,
    endpoint=["http://localhost:8003/submit"]
)

logger = setup_logger("GroceryAgent")

# Define the Chat Protocol v0.3.0 for ASI:One compatibility
grocery_protocol = Protocol("chat", version="0.3.0")

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


def search_and_price_ingredient(ingredient_name: str, quantity: float, unit: str) -> Dict[str, Any]:
    """
    Search Kroger API for ingredient and get real pricing and product details.
    Returns dict with: name, quantity, unit, price, product_id, upc, brand, category
    
    Falls back to estimated price only if Kroger API fails.
    """
    # Try Kroger API FIRST (this is the primary method)
    kroger_product = search_kroger_product(ingredient_name)
    
    if kroger_product and kroger_product.get("price"):
        # Successfully found on Kroger!
        price = float(kroger_product["price"])
        log_agent_message("GroceryAgent", f"✅ Found '{ingredient_name}' on Kroger: ${price} (Product ID: {kroger_product.get('product_id', 'N/A')})")
        
        return {
            "name": kroger_product.get("name", ingredient_name),
            "quantity": quantity,
            "unit": unit,
            "price": price,
            "product_id": kroger_product.get("product_id"),
            "upc": kroger_product.get("upc"),
            "brand": kroger_product.get("brand"),
            "category": categorize_ingredient(ingredient_name),
            "source": "kroger_api"
        }
    
    # Fallback ONLY if Kroger API failed
    logger.warning(f"Kroger API failed for '{ingredient_name}', using fallback price estimate")
    
    ingredient_lower = ingredient_name.lower()
    estimated_price = 3.99  # Default
    
    # Try to find a reasonable estimate
    if ingredient_lower in INGREDIENT_PRICES:
        estimated_price = INGREDIENT_PRICES[ingredient_lower]
    else:
        # Try partial match
        for key, price in INGREDIENT_PRICES.items():
            if key in ingredient_lower:
                estimated_price = price
                break
    
    return {
        "name": ingredient_name,
        "quantity": quantity,
        "unit": unit,
        "price": estimated_price,
        "product_id": None,
        "upc": None,
        "brand": "Generic",
        "category": categorize_ingredient(ingredient_name),
        "source": "estimated"
    }


def create_grocery_list(recipe: Dict[str, Any], store: str = "Kroger") -> Tuple[Dict[str, Any], List[str]]:
    """
    Create a grocery list from recipe ingredients using Kroger API.
    
    Searches Kroger for each ingredient to get real prices, product IDs, and details.
    Falls back to estimates only if Kroger API is unavailable.
    Returns (grocery_list_dict, tools_called_list)
    
    TOOL: create_grocery_list - Main grocery list creation function
    
    Args:
        recipe: Recipe dictionary with structured ingredients
        store: Preferred store name (default: Kroger)
    
    Returns:
        Tuple of (grocery list dict, list of tools called)
    """
    tools_called = ["create_grocery_list"]
    ingredients = recipe.get("ingredients", [])
    
    grocery_items = []
    total_cost = 0.0
    kroger_items_found = 0
    
    log_agent_message("GroceryAgent", f"🔍 Searching Kroger for {len(ingredients)} ingredients...")
    
    for ingredient in ingredients:
        # Handle both old dict format and new Ingredient object format
        if isinstance(ingredient, dict):
            # Check if it's the new structured format
            if "quantity" in ingredient and "unit" in ingredient:
                item_name = ingredient.get("name", "Unknown")
                quantity = ingredient.get("quantity", 1.0)
                unit = ingredient.get("unit", "")
                notes = ingredient.get("notes", "")
            else:
                # Old format with quantity as string
                item_name = ingredient.get("name", "Unknown")
                quantity_str = ingredient.get("quantity", "1")
                # Try to parse quantity and unit from string like "200g" or "1 cup"
                import re
                match = re.match(r"([\d.]+)\s*([a-zA-Z]*)", str(quantity_str))
                if match:
                    quantity = float(match.group(1))
                    unit = match.group(2) or "unit"
                else:
                    quantity = 1.0
                    unit = "unit"
                notes = ""
        else:
            # It's an Ingredient object (Pydantic model)
            item_name = getattr(ingredient, 'name', 'Unknown')
            quantity = getattr(ingredient, 'quantity', 1.0)
            unit = getattr(ingredient, 'unit', 'unit')
            notes = getattr(ingredient, 'notes', '') or ''
        
        # Search Kroger API and get pricing details
        item_details = search_and_price_ingredient(item_name, quantity, unit)
        tools_called.append("search_and_price_ingredient")
        
        if item_details.get("source") == "kroger_api":
            kroger_items_found += 1
            tools_called.append("kroger_api_success")
        
        # Format quantity display
        quantity_display = f"{quantity} {unit}".strip()
        if notes:
            quantity_display += f" ({notes})"
        
        grocery_item = GroceryItem(
            name=item_details["name"],
            quantity=quantity_display,
            category=item_details["category"],
            estimated_price=item_details["price"]
        )
        
        # Add extra metadata if from Kroger
        if item_details.get("product_id"):
            grocery_item.product_id = item_details["product_id"]
            grocery_item.upc = item_details["upc"]
            grocery_item.brand = item_details["brand"]
        
        grocery_items.append(grocery_item)
        total_cost += item_details["price"]
    
    # Log results
    if kroger_items_found > 0:
        log_agent_message("GroceryAgent", f"✅ Found {kroger_items_found}/{len(ingredients)} items on Kroger with real prices!")
    else:
        log_agent_message("GroceryAgent", f"⚠️ Kroger API unavailable, using estimated prices")
        tools_called.append("fallback_pricing")
    
    return {
        "store": store,
        "items": grocery_items,
        "total_estimated_cost": round(total_cost, 2),
        "kroger_items_found": kroger_items_found,
        "total_items": len(ingredients)
    }, tools_called


@grocery_agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup handler"""
    log_agent_message("GroceryAgent", "🚀 GroceryAgent started and ready!")
    log_agent_message("GroceryAgent", "📡 Chat Protocol v0.3.0 enabled for ASI:One")
    logger.info(f"Agent address: {ctx.agent.address}")


@grocery_agent.on_message(model=GroceryRequest)
async def handle_grocery_request(ctx: Context, sender: str, msg: GroceryRequest):
    """
    Main message handler for GroceryAgent.
    Compatible with ASI:One Chat Protocol v0.3.0
    Uses Kroger API for real grocery pricing.
    """
    log_agent_message("GroceryAgent", "📨 Received grocery list request")
    
    tools_called = ["handle_grocery_request"]
    
    try:
        # Create grocery list
        grocery_data, list_tools = create_grocery_list(msg.recipe, msg.store_preference)
        tools_called.extend(list_tools)
        
        # Generate Kroger or store-specific order URL
        recipe_title = msg.recipe.get("title", "recipe").replace(" ", "-").lower()
        if msg.store_preference.lower() == "kroger":
            order_url = f"https://www.kroger.com/cart?recipe={recipe_title}"
        else:
            order_url = f"https://instacart.com/order/{msg.user_id}/{recipe_title}"
        
        kroger_count = grocery_data.get("kroger_items_found", 0)
        total_items = grocery_data.get("total_items", len(grocery_data["items"]))
        
        if kroger_count > 0:
            price_source = f"{kroger_count}/{total_items} prices from Kroger API"
        else:
            price_source = "estimated prices (Kroger API unavailable)"
        
        response = GroceryResponse(
            store=grocery_data["store"],
            items=grocery_data["items"],
            total_estimated_cost=grocery_data["total_estimated_cost"],
            kroger_items_found=kroger_count,
            total_items=total_items,
            message=f"Created grocery list with {len(grocery_data['items'])} items ({price_source}). Total: ${grocery_data['total_estimated_cost']}",
            order_url=order_url,
            next_action="review_order",
            tools_called=tools_called,
            llm_provider="kroger_api" if kroger_count > 0 else "estimated"
        )
        
        log_agent_message("GroceryAgent", f"✅ Created list with {len(grocery_data['items'])} items")
        log_agent_message("GroceryAgent", f"🔧 Tools called: {', '.join(tools_called)}")
        
        # Send response back
        await ctx.send(sender, response)
        
    except Exception as e:
        logger.error(f"Error creating grocery list: {e}")
        tools_called.append("error_handler")
        error_response = GroceryResponse(
            store="Kroger",
            items=[],
            total_estimated_cost=0.0,
            kroger_items_found=0,
            total_items=0,
            message=f"Sorry, I encountered an error: {str(e)}",
            next_action="retry",
            tools_called=tools_called,
            llm_provider="error"
        )
        await ctx.send(sender, error_response)


@grocery_protocol.on_message(model=GroceryRequest)
async def handle_grocery_protocol_message(ctx: Context, sender: str, msg: GroceryRequest):
    """
    Chat Protocol v0.3.0 handler for ASI:One compatibility.
    Creates grocery lists based on selected recipes from other agents.
    This is the official protocol handler for Agentverse discovery.
    Uses Kroger API for real grocery pricing.
    """
    ctx.logger.info(f"[Chat Protocol v0.3.0] Received grocery request from {sender}")
    log_agent_message("GroceryAgent", f"[Protocol] Creating grocery list for {sender}")
    
    tools_called = ["handle_grocery_protocol_message"]
    
    try:
        # Create grocery list using Kroger API
        grocery_data, list_tools = create_grocery_list(msg.recipe, msg.store_preference)
        tools_called.extend(list_tools)
        
        # Generate store-specific order URL
        recipe_title = msg.recipe.get("title", "recipe").replace(" ", "-").lower()
        if msg.store_preference.lower() == "kroger":
            order_url = f"https://www.kroger.com/cart?recipe={recipe_title}"
        else:
            order_url = f"https://instacart.com/order/{msg.user_id}/{recipe_title}"
        
        kroger_count = grocery_data.get("kroger_items_found", 0)
        total_items = grocery_data.get("total_items", len(grocery_data["items"]))
        
        if kroger_count > 0:
            price_source = f"{kroger_count}/{total_items} prices from Kroger API"
        else:
            price_source = "estimated prices (Kroger API unavailable)"
        
        response = GroceryResponse(
            store=grocery_data["store"],
            items=grocery_data["items"],
            total_estimated_cost=grocery_data["total_estimated_cost"],
            kroger_items_found=kroger_count,
            total_items=total_items,
            message=f"Created grocery list with {len(grocery_data['items'])} items ({price_source}). Total: ${grocery_data['total_estimated_cost']}",
            order_url=order_url,
            next_action="review_order",
            tools_called=tools_called,
            llm_provider="kroger_api" if kroger_count > 0 else "estimated"
        )
        
        ctx.logger.info(f"[Chat Protocol v0.3.0] Created list with {len(grocery_data['items'])} items, sending to {sender}")
        ctx.logger.info(f"[Chat Protocol v0.3.0] Tools called: {', '.join(tools_called)}")
        log_agent_message("GroceryAgent", f"✅ [Protocol] Sent grocery list to {sender}")
        
        # Send response back
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"[Chat Protocol v0.3.0] Error creating grocery list: {e}")
        logger.error(f"Error creating grocery list: {e}")
        tools_called.append("error_handler")
        error_response = GroceryResponse(
            store="Kroger",
            items=[],
            total_estimated_cost=0.0,
            kroger_items_found=0,
            total_items=0,
            message=f"Sorry, I encountered an error: {str(e)}",
            next_action="retry",
            tools_called=tools_called,
            llm_provider="error"
        )
        await ctx.send(sender, error_response)


# Include the Chat Protocol v0.3.0 for ASI:One and Agentverse
grocery_agent.include(grocery_protocol)


def generate_grocery_list(grocery_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper for grocery list generation.
    Used by FastAPI endpoints.
    Uses Kroger API with tool tracking.
    """
    tools_called = ["generate_grocery_list"]
    
    request = GroceryRequest(**grocery_request)
    grocery_data, list_tools = create_grocery_list(request.recipe, request.store_preference)
    tools_called.extend(list_tools)
    
    # Generate store-specific order URL
    recipe_title = request.recipe.get("title", "recipe").replace(" ", "-").lower()
    if request.store_preference.lower() == "kroger":
        order_url = f"https://www.kroger.com/cart?recipe={recipe_title}"
    else:
        order_url = f"https://instacart.com/order/{request.user_id}/{recipe_title}"
    
    kroger_count = grocery_data.get("kroger_items_found", 0)
    total_items = grocery_data.get("total_items", len(grocery_data["items"]))
    
    if kroger_count > 0:
        price_source = f"{kroger_count}/{total_items} prices from Kroger API"
    else:
        price_source = "estimated prices (Kroger API unavailable)"
    
    return {
        "agent": "GroceryAgent",
        "store": grocery_data["store"],
        "items": [item.model_dump() for item in grocery_data["items"]],
        "total_estimated_cost": grocery_data["total_estimated_cost"],
        "kroger_items_found": kroger_count,
        "total_items": total_items,
        "message": f"Created grocery list with {len(grocery_data['items'])} items ({price_source}). Total: ${grocery_data['total_estimated_cost']}",
        "order_url": order_url,
        "next_action": "review_order",
        "tools_called": tools_called,
        "llm_provider": "kroger_api" if kroger_count > 0 else "estimated"
    }


if __name__ == "__main__":
    log_agent_message("GroceryAgent", "Starting GroceryAgent...")
    grocery_agent.run()

