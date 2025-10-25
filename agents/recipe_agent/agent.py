"""
RecipeAgent - Recipe Generator for Agentic Grocery
Generates personalized meal options based on user profile and preferences.
Uses Claude API for intelligent recipe generation.
ASI:One compatible with Chat Protocol v0.3.0

Agent Metadata:
- Name: RecipeAgent
- Description: Intelligent recipe generator that creates personalized meal options 
               based on user preferences, dietary goals, and macros
- Tags: nutrition, recipes, meal-planning, fetchai, agentic-ai, claude
- Endpoint: http://localhost:8000/recipe
- Version: 0.3.0
- Protocol: chat-protocol-v0.3.0
"""

import os
import json
from typing import Dict, Any, List, Optional
from uagents import Agent, Context, Model
from pydantic import BaseModel, Field
import sys
from anthropic import Anthropic

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.logger import setup_logger, log_agent_message


# Pydantic models for structured communication
class RecipeRequest(BaseModel):
    """Recipe generation request model"""
    user_profile: Dict[str, Any]
    preferences: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class Recipe(BaseModel):
    """Individual recipe model"""
    title: str = Field(..., description="Recipe title")
    description: str = Field(..., description="Short description")
    cook_time: str = Field(..., description="Cooking time")
    servings: int = Field(default=1, description="Number of servings")
    macros: Dict[str, float] = Field(..., description="Macronutrients")
    ingredients: List[Dict[str, str]] = Field(..., description="List of ingredients with quantities")
    instructions: List[str] = Field(..., description="Cooking instructions")
    image_url: str = Field(..., description="Recipe image URL")
    cuisine: Optional[str] = None
    difficulty: str = Field(default="medium", description="Difficulty level")


class RecipeResponse(BaseModel):
    """Recipe generation response model"""
    agent: str = Field(default="RecipeAgent", description="Agent name")
    recipes: List[Recipe] = Field(..., description="List of generated recipes")
    message: str = Field(..., description="Response message")
    next_action: Optional[str] = Field(default="select_recipe", description="Next action")


# Initialize RecipeAgent
RECIPE_AGENT_SEED = os.getenv("RECIPE_AGENT_SEED", "recipe-agent-seed-67890")
recipe_agent = Agent(
    name="RecipeAgent",
    seed=RECIPE_AGENT_SEED,
    port=8002,
    endpoint=["http://localhost:8002/submit"]
)

logger = setup_logger("RecipeAgent")


def calculate_target_macros(user_profile: Dict[str, Any], meal_type: str) -> Dict[str, float]:
    """
    Calculate target macros for a specific meal based on user profile.
    Distributes daily macros across meals.
    """
    target_macros = user_profile.get("target_macros", {
        "protein_g": 140,
        "carbs_g": 200,
        "fat_g": 50,
        "calories": 1800
    })
    
    # Distribution by meal type
    meal_distribution = {
        "breakfast": 0.25,
        "lunch": 0.35,
        "dinner": 0.30,
        "snack": 0.10
    }
    
    ratio = meal_distribution.get(meal_type, 0.33)
    
    return {
        "protein_g": round(target_macros["protein_g"] * ratio, 1),
        "carbs_g": round(target_macros["carbs_g"] * ratio, 1),
        "fat_g": round(target_macros["fat_g"] * ratio, 1),
        "calories": round(target_macros["calories"] * ratio, 0)
    }


def generate_recipes_with_claude(request: RecipeRequest) -> List[Recipe]:
    """
    Generate recipes using Claude API based on user preferences.
    Falls back to mock data if API key is not configured.
    """
    user_profile = request.user_profile
    preferences = request.preferences
    meal_type = preferences.get("meal_type", "lunch")
    cuisine = preferences.get("cuisine", "indian")
    diet = preferences.get("dietary_restrictions", "vegetarian")
    cook_time = preferences.get("cook_time", "30-45 mins")
    
    target_macros = calculate_target_macros(user_profile, meal_type)
    
    # Try Claude API if key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your_anthropic_api_key_here":
        try:
            client = Anthropic(api_key=api_key)
            
            prompt = f"""Generate 3 {diet} {cuisine} recipes for {meal_type} with the following requirements:
- Cook time: {cook_time}
- Target macros per serving: {target_macros['protein_g']}g protein, {target_macros['carbs_g']}g carbs, {target_macros['fat_g']}g fat, {target_macros['calories']} calories
- User likes: {', '.join(user_profile.get('likes', []))}
- User dislikes: {', '.join(user_profile.get('dislikes', []))}

For each recipe, provide:
1. Title (creative and appetizing)
2. Short description (1-2 sentences)
3. Exact macros (protein_g, carbs_g, fat_g, calories, fiber_g)
4. Detailed ingredients list with quantities
5. Step-by-step instructions
6. Difficulty level (easy/medium/hard)

Return as valid JSON array with this structure:
[{{
  "title": "Recipe Name",
  "description": "Brief description",
  "cook_time": "{cook_time}",
  "servings": 1,
  "macros": {{"protein_g": X, "carbs_g": Y, "fat_g": Z, "calories": N, "fiber_g": F}},
  "ingredients": [{{"name": "ingredient", "quantity": "amount"}}],
  "instructions": ["step 1", "step 2"],
  "cuisine": "{cuisine}",
  "difficulty": "medium"
}}]"""

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse Claude response
            response_text = response.content[0].text
            # Extract JSON from response (Claude might wrap it in markdown)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            recipes_data = json.loads(response_text.strip())
            
            # Convert to Recipe objects with image URLs
            recipes = []
            for i, recipe_data in enumerate(recipes_data[:3]):
                recipe_data["image_url"] = f"https://api.placeholder.com/recipe-{i+1}.jpg"
                recipes.append(Recipe(**recipe_data))
            
            log_agent_message("RecipeAgent", f"✨ Generated {len(recipes)} recipes using Claude API")
            return recipes
            
        except Exception as e:
            logger.warning(f"Claude API error: {e}. Falling back to mock recipes.")
    
    # Fallback to mock recipes
    return generate_mock_recipes(request)


def generate_mock_recipes(request: RecipeRequest) -> List[Recipe]:
    """
    Generate mock recipes based on user preferences.
    Used as fallback when Claude API is not available.
    """
    user_profile = request.user_profile
    preferences = request.preferences
    meal_type = preferences.get("meal_type", "lunch")
    cuisine = preferences.get("cuisine", "indian")
    diet = preferences.get("dietary_restrictions", "vegetarian")
    
    target_macros = calculate_target_macros(user_profile, meal_type)
    
    # Mock recipe templates based on preferences
    if diet == "vegetarian" and cuisine == "indian":
        recipes = [
            Recipe(
                title="Paneer Tikka with Quinoa",
                description="Grilled cottage cheese marinated in spices, served with protein-rich quinoa",
                cook_time=preferences.get("cook_time", "30-45 mins"),
                servings=1,
                macros={
                    "protein_g": target_macros["protein_g"],
                    "carbs_g": target_macros["carbs_g"],
                    "fat_g": target_macros["fat_g"],
                    "calories": target_macros["calories"],
                    "fiber_g": 8.0
                },
                ingredients=[
                    {"name": "paneer (cottage cheese)", "quantity": "200g"},
                    {"name": "quinoa", "quantity": "1/2 cup"},
                    {"name": "yogurt", "quantity": "1/4 cup"},
                    {"name": "garam masala", "quantity": "1 tsp"},
                    {"name": "turmeric", "quantity": "1/2 tsp"},
                    {"name": "bell peppers", "quantity": "1 cup"},
                    {"name": "onions", "quantity": "1 medium"}
                ],
                instructions=[
                    "Marinate paneer cubes in yogurt, garam masala, and turmeric for 20 mins",
                    "Cook quinoa according to package instructions",
                    "Grill paneer and vegetables on skewers or pan",
                    "Serve paneer tikka over quinoa bed",
                    "Garnish with fresh cilantro and lemon"
                ],
                image_url="https://example.com/images/paneer-tikka-quinoa.jpg",
                cuisine="Indian",
                difficulty="medium"
            ),
            Recipe(
                title="Spicy Chickpea Buddha Bowl",
                description="Protein-packed chickpeas with roasted vegetables and tahini dressing",
                cook_time=preferences.get("cook_time", "30-45 mins"),
                servings=1,
                macros={
                    "protein_g": target_macros["protein_g"] * 0.9,
                    "carbs_g": target_macros["carbs_g"] * 1.1,
                    "fat_g": target_macros["fat_g"] * 0.95,
                    "calories": target_macros["calories"],
                    "fiber_g": 12.0
                },
                ingredients=[
                    {"name": "chickpeas (cooked)", "quantity": "1.5 cups"},
                    {"name": "sweet potato", "quantity": "1 medium"},
                    {"name": "spinach", "quantity": "2 cups"},
                    {"name": "tahini", "quantity": "2 tbsp"},
                    {"name": "cumin", "quantity": "1 tsp"},
                    {"name": "chili powder", "quantity": "1/2 tsp"},
                    {"name": "brown rice", "quantity": "1/2 cup cooked"}
                ],
                instructions=[
                    "Roast chickpeas with spices at 400°F for 25 mins",
                    "Cube and roast sweet potato until tender",
                    "Prepare brown rice base in bowl",
                    "Sauté spinach with garlic",
                    "Arrange all components in bowl and drizzle tahini dressing"
                ],
                image_url="https://example.com/images/chickpea-buddha-bowl.jpg",
                cuisine="Indian-fusion",
                difficulty="easy"
            ),
            Recipe(
                title="Dal Tadka with Roti",
                description="Protein-rich lentil curry with whole wheat flatbread",
                cook_time=preferences.get("cook_time", "30-45 mins"),
                servings=1,
                macros={
                    "protein_g": target_macros["protein_g"] * 1.05,
                    "carbs_g": target_macros["carbs_g"],
                    "fat_g": target_macros["fat_g"] * 0.9,
                    "calories": target_macros["calories"],
                    "fiber_g": 10.0
                },
                ingredients=[
                    {"name": "toor dal (split pigeon peas)", "quantity": "3/4 cup"},
                    {"name": "whole wheat flour", "quantity": "1 cup"},
                    {"name": "tomatoes", "quantity": "2 medium"},
                    {"name": "cumin seeds", "quantity": "1 tsp"},
                    {"name": "ghee", "quantity": "1 tbsp"},
                    {"name": "ginger-garlic paste", "quantity": "1 tsp"},
                    {"name": "green chilies", "quantity": "2"}
                ],
                instructions=[
                    "Pressure cook dal with turmeric until soft",
                    "Prepare tadka: heat ghee, add cumin, chilies, and spices",
                    "Add tomatoes and cook until soft",
                    "Mix tadka with cooked dal",
                    "Make roti with whole wheat flour",
                    "Serve dal with fresh roti"
                ],
                image_url="https://example.com/images/dal-tadka-roti.jpg",
                cuisine="Indian",
                difficulty="medium"
            )
        ]
    else:
        # Generic healthy meal options
        recipes = [
            Recipe(
                title=f"Healthy {meal_type.capitalize()} Option 1",
                description=f"Nutritious {cuisine} style {meal_type}",
                cook_time=preferences.get("cook_time", "30 mins"),
                servings=1,
                macros=target_macros,
                ingredients=[
                    {"name": "main protein", "quantity": "200g"},
                    {"name": "vegetables", "quantity": "2 cups"},
                    {"name": "whole grains", "quantity": "1 cup"}
                ],
                instructions=[
                    "Prepare protein source",
                    "Cook vegetables",
                    "Combine with grains",
                    "Season to taste"
                ],
                image_url=f"https://example.com/images/{meal_type}-option-1.jpg",
                cuisine=cuisine,
                difficulty="medium"
            )
        ]
    
    return recipes[:3]  # Return top 3 recipes


@recipe_agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup handler"""
    log_agent_message("RecipeAgent", "🚀 RecipeAgent started and ready!")
    logger.info(f"Agent address: {ctx.agent.address}")


@recipe_agent.on_message(model=RecipeRequest)
async def handle_recipe_request(ctx: Context, sender: str, msg: RecipeRequest):
    """
    Main message handler for RecipeAgent.
    Compatible with ASI:One Chat Protocol v0.3.0
    """
    log_agent_message("RecipeAgent", "📨 Received recipe generation request")
    
    try:
        # Generate recipes using Claude API or mock data
        recipes = generate_recipes_with_claude(msg)
        
        response = RecipeResponse(
            recipes=recipes,
            message=f"Here are {len(recipes)} personalized recipe options for you!",
            next_action="select_recipe"
        )
        
        log_agent_message("RecipeAgent", f"✅ Generated {len(recipes)} recipes")
        
        # Send response back
        await ctx.send(sender, response)
        
    except Exception as e:
        logger.error(f"Error generating recipes: {e}")
        error_response = RecipeResponse(
            recipes=[],
            message=f"Sorry, I encountered an error: {str(e)}",
            next_action="retry"
        )
        await ctx.send(sender, error_response)


def generate_recipes(recipe_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper for recipe generation.
    Used by FastAPI endpoints.
    """
    request = RecipeRequest(**recipe_request)
    recipes = generate_recipes_with_claude(request)
    
    return {
        "agent": "RecipeAgent",
        "recipes": [recipe.model_dump() for recipe in recipes],
        "message": f"Here are {len(recipes)} personalized recipe options for you!",
        "next_action": "select_recipe"
    }


if __name__ == "__main__":
    log_agent_message("RecipeAgent", "Starting RecipeAgent...")
    recipe_agent.run()

