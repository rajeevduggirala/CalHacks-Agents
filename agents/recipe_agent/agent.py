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
from uagents import Agent, Context, Model, Protocol
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


class Ingredient(BaseModel):
    """Structured ingredient model"""
    name: str = Field(..., description="Ingredient name (e.g., 'paneer', 'quinoa')")
    quantity: float = Field(..., description="Numeric quantity")
    unit: str = Field(..., description="Unit of measurement (e.g., 'g', 'cup', 'tbsp', 'whole')")
    notes: Optional[str] = Field(default=None, description="Additional notes (e.g., 'diced', 'chopped')")
    
    def to_string(self) -> str:
        """Convert to readable string"""
        base = f"{self.quantity} {self.unit} {self.name}"
        if self.notes:
            base += f" ({self.notes})"
        return base


class Recipe(BaseModel):
    """Individual recipe model with structured data"""
    title: str = Field(..., description="Recipe title")
    description: str = Field(..., description="Short description (1-2 sentences)")
    cook_time: str = Field(..., description="Total cooking time")
    prep_time: str = Field(..., description="Preparation time")
    servings: int = Field(default=1, description="Number of servings")
    macros: Dict[str, float] = Field(..., description="Macronutrients per serving")
    ingredients: List[Ingredient] = Field(..., description="Structured list of ingredients with quantities")
    instructions: str = Field(..., description="Cooking instructions in markdown format")
    image_url: str = Field(..., description="AI-generated recipe image URL")
    cuisine: Optional[str] = None
    difficulty: str = Field(default="medium", description="Difficulty level (easy/medium/hard)")
    tags: List[str] = Field(default_factory=list, description="Recipe tags")


class RecipeResponse(BaseModel):
    """Recipe generation response model"""
    agent: str = Field(default="RecipeAgent", description="Agent name")
    recipes: List[Recipe] = Field(..., description="List of generated recipes")
    message: str = Field(..., description="Response message")
    next_action: Optional[str] = Field(default="select_recipe", description="Next action")
    tools_called: Optional[List[str]] = Field(default=None, description="List of tools/functions called")
    llm_provider: Optional[str] = Field(default="claude", description="LLM provider used")


# Initialize RecipeAgent
RECIPE_AGENT_SEED = os.getenv("RECIPE_AGENT_SEED", "recipe-agent-seed-67890")
recipe_agent = Agent(
    name="RecipeAgent",
    seed=RECIPE_AGENT_SEED,
    port=8002,
    endpoint=["http://localhost:8002/submit"]
)

logger = setup_logger("RecipeAgent")

# Define the Chat Protocol v0.3.0 for ASI:One compatibility
recipe_protocol = Protocol("chat", version="0.3.0")


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


def generate_recipe_image(recipe_title: str, description: str) -> str:
    """
    Generate recipe image using AI image generation.
    Uses free AI image generation API (Pollinations.ai) or falls back to placeholder.
    """
    try:
        # Use free AI image generation service
        # Create descriptive prompt for better images
        prompt = f"professional food photography of {recipe_title}, {description}, high quality, appetizing, well plated, natural lighting"
        # URL encode the prompt
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Pollinations.ai provides free AI-generated images
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
        
        logger.info(f"🖼️  Generated image URL for '{recipe_title}': {image_url[:100]}...")
        log_agent_message("RecipeAgent", f"Generated AI image for recipe: {recipe_title}")
        
        return image_url
        
    except Exception as e:
        logger.warning(f"Image generation error: {e}")
        # Fallback to simple placeholder
        safe_title = recipe_title.replace(' ', '+')
        fallback_url = f"https://via.placeholder.com/512x512/FF6B6B/FFFFFF?text={safe_title}"
        logger.info(f"Using fallback image: {fallback_url}")
        return fallback_url


def format_instructions_markdown(steps: List[str]) -> str:
    """
    Format cooking instructions as beautiful markdown.
    """
    markdown = "## 👨‍🍳 Cooking Instructions\n\n"
    
    for i, step in enumerate(steps, 1):
        # Add step number and formatting
        markdown += f"### Step {i}\n"
        markdown += f"{step}\n\n"
        
        # Add helpful emojis based on keywords
        if any(word in step.lower() for word in ['heat', 'boil', 'cook']):
            markdown += "🔥 "
        if any(word in step.lower() for word in ['mix', 'stir', 'combine']):
            markdown += "🥄 "
        if any(word in step.lower() for word in ['chop', 'cut', 'slice']):
            markdown += "🔪 "
        if any(word in step.lower() for word in ['serve', 'plate', 'garnish']):
            markdown += "🍽️ "
        
        markdown += "\n---\n\n"
    
    markdown += "### ✅ Done!\nYour delicious meal is ready to serve!\n"
    return markdown


def generate_recipes_with_claude(request: RecipeRequest) -> tuple[List[Recipe], List[str]]:
    """
    Generate 4-5 recipes using Claude API with structured ingredients and markdown instructions.
    Falls back to mock data if API key is not configured.
    Returns (recipes_list, tools_called_list)
    
    TOOL: generate_recipes_with_claude - Main recipe generation function
    """
    tools_called = ["generate_recipes_with_claude"]
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
            
            prompt = f"""Generate 4-5 diverse {diet} {cuisine} recipes for {meal_type}. Each recipe must be unique and interesting.

Requirements:
- Cook time: {cook_time}
- Target macros per serving: {target_macros['protein_g']}g protein, {target_macros['carbs_g']}g carbs, {target_macros['fat_g']}g fat, {target_macros['calories']} calories
- User likes: {', '.join(user_profile.get('likes', []))}
- User dislikes: {', '.join(user_profile.get('dislikes', []))}

CRITICAL: Ingredients MUST be structured with name, quantity (as a number), and unit separately!

Return ONLY valid JSON (no markdown formatting) with this EXACT structure:
[{{
  "title": "Creative Recipe Name",
  "description": "Appetizing 1-2 sentence description",
  "prep_time": "10 mins",
  "cook_time": "20 mins",
  "servings": 1,
  "macros": {{"protein_g": 45.5, "carbs_g": 60.0, "fat_g": 15.0, "calories": 540, "fiber_g": 8.0}},
  "ingredients": [
    {{"name": "paneer", "quantity": 200, "unit": "g", "notes": "cubed"}},
    {{"name": "quinoa", "quantity": 0.5, "unit": "cup", "notes": "uncooked"}},
    {{"name": "olive oil", "quantity": 1, "unit": "tbsp", "notes": null}}
  ],
  "instructions": [
    "Heat olive oil in a large pan over medium heat.",
    "Add cubed paneer and cook until golden brown, about 5 minutes.",
    "Meanwhile, rinse quinoa and cook according to package directions.",
    "Combine cooked quinoa with paneer and season to taste.",
    "Serve hot, garnished with fresh herbs."
  ],
  "cuisine": "{cuisine}",
  "difficulty": "medium",
  "tags": ["high-protein", "vegetarian", "dinner"]
}}]"""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=6000,
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
            
            # Convert to Recipe objects with structured data
            recipes = []
            for recipe_data in recipes_data[:5]:  # Max 5 recipes
                # Convert instructions to markdown
                instructions_list = recipe_data.get("instructions", [])
                recipe_data["instructions"] = format_instructions_markdown(instructions_list)
                
                # Convert ingredients to Ingredient objects
                ingredients = []
                for ing in recipe_data.get("ingredients", []):
                    if isinstance(ing, dict):
                        ingredients.append(Ingredient(**ing))
                    else:
                        # Handle old format
                        ingredients.append(Ingredient(
                            name=ing.get("name", "ingredient"),
                            quantity=1.0,
                            unit="serving",
                            notes=ing.get("quantity", "")
                        ))
                recipe_data["ingredients"] = ingredients
                
                # Generate AI image
                recipe_data["image_url"] = generate_recipe_image(
                    recipe_data["title"],
                    recipe_data["description"]
                )
                
                recipes.append(Recipe(**recipe_data))
            
            log_agent_message("RecipeAgent", f"✨ Generated {len(recipes)} recipes using Claude API")
            tools_called.append("claude_api_call")
            tools_called.append("generate_recipe_image")
            return recipes, tools_called
            
        except Exception as e:
            logger.warning(f"Claude API error: {e}. Falling back to mock recipes.")
            logger.debug(f"Full error: {str(e)}")
            tools_called.append("claude_api_error")
    
    # Fallback to mock recipes
    tools_called.append("generate_mock_recipes_fallback")
    mock_recipes = generate_mock_recipes(request)
    return mock_recipes, tools_called


def generate_mock_recipes(request: RecipeRequest) -> List[Recipe]:
    """
    Generate mock recipes based on user preferences with structured ingredients.
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
                title="Paneer Tikka with Quinoa Bowl",
                description="Grilled cottage cheese marinated in aromatic spices, served with protein-rich quinoa and colorful vegetables",
                prep_time="15 mins",
                cook_time="30 mins",
                servings=1,
                macros={
                    "protein_g": target_macros["protein_g"],
                    "carbs_g": target_macros["carbs_g"],
                    "fat_g": target_macros["fat_g"],
                    "calories": target_macros["calories"],
                    "fiber_g": 8.0
                },
                ingredients=[
                    Ingredient(name="paneer", quantity=200, unit="g", notes="cubed"),
                    Ingredient(name="quinoa", quantity=0.5, unit="cup", notes="uncooked"),
                    Ingredient(name="yogurt", quantity=0.25, unit="cup", notes="Greek yogurt"),
                    Ingredient(name="garam masala", quantity=1, unit="tsp", notes=None),
                    Ingredient(name="turmeric", quantity=0.5, unit="tsp", notes=None),
                    Ingredient(name="bell peppers", quantity=1, unit="cup", notes="diced"),
                    Ingredient(name="onions", quantity=1, unit="whole", notes="medium, sliced")
                ],
                instructions=format_instructions_markdown([
                    "Mix yogurt, garam masala, and turmeric in a bowl. Add cubed paneer and marinate for 20 minutes.",
                    "Rinse quinoa thoroughly and cook according to package directions (usually 15 minutes).",
                    "Heat a grill pan or skillet over medium-high heat. Thread paneer and vegetables onto skewers.",
                    "Grill paneer and vegetables for 8-10 minutes, turning occasionally until golden brown.",
                    "Fluff the cooked quinoa with a fork and place in serving bowl.",
                    "Top quinoa with grilled paneer tikka and vegetables. Garnish with fresh cilantro and lemon wedges."
                ]),
                image_url=generate_recipe_image("Paneer Tikka with Quinoa Bowl", "Grilled spiced cottage cheese with quinoa"),
                cuisine="Indian",
                difficulty="medium",
                tags=["high-protein", "vegetarian", "indian", "grilled"]
            ),
            Recipe(
                title="Spicy Chickpea Buddha Bowl",
                description="Protein-packed roasted chickpeas with colorful roasted vegetables, tahini dressing, and brown rice",
                prep_time="10 mins",
                cook_time="35 mins",
                servings=1,
                macros={
                    "protein_g": target_macros["protein_g"] * 0.9,
                    "carbs_g": target_macros["carbs_g"] * 1.1,
                    "fat_g": target_macros["fat_g"] * 0.95,
                    "calories": target_macros["calories"],
                    "fiber_g": 12.0
                },
                ingredients=[
                    Ingredient(name="chickpeas", quantity=1.5, unit="cup", notes="cooked, drained"),
                    Ingredient(name="sweet potato", quantity=1, unit="whole", notes="medium, cubed"),
                    Ingredient(name="spinach", quantity=2, unit="cup", notes="fresh"),
                    Ingredient(name="tahini", quantity=2, unit="tbsp", notes=None),
                    Ingredient(name="cumin", quantity=1, unit="tsp", notes="ground"),
                    Ingredient(name="chili powder", quantity=0.5, unit="tsp", notes=None),
                    Ingredient(name="brown rice", quantity=0.5, unit="cup", notes="cooked")
                ],
                instructions=format_instructions_markdown([
                    "Preheat oven to 400°F (200°C). Toss chickpeas with cumin and chili powder.",
                    "Spread chickpeas on a baking sheet and roast for 25 minutes until crispy.",
                    "Meanwhile, toss cubed sweet potato with a bit of oil and roast for 20-25 minutes.",
                    "In a large pan, sauté spinach with minced garlic until wilted, about 3 minutes.",
                    "Prepare brown rice base in your serving bowl.",
                    "Arrange roasted chickpeas, sweet potato, and sautéed spinach over rice.",
                    "Drizzle with tahini dressing and serve immediately."
                ]),
                image_url=generate_recipe_image("Spicy Chickpea Buddha Bowl", "Roasted chickpeas with vegetables"),
                cuisine="Indian-fusion",
                difficulty="easy",
                tags=["plant-based", "high-fiber", "roasted", "bowl"]
            ),
            Recipe(
                title="Dal Tadka with Whole Wheat Roti",
                description="Creamy yellow lentil curry tempered with aromatic spices, served with fresh whole wheat flatbread",
                prep_time="10 mins",
                cook_time="35 mins",
                servings=1,
                macros={
                    "protein_g": target_macros["protein_g"] * 1.05,
                    "carbs_g": target_macros["carbs_g"],
                    "fat_g": target_macros["fat_g"] * 0.9,
                    "calories": target_macros["calories"],
                    "fiber_g": 10.0
                },
                ingredients=[
                    Ingredient(name="toor dal", quantity=0.75, unit="cup", notes="split pigeon peas"),
                    Ingredient(name="whole wheat flour", quantity=1, unit="cup", notes="for roti"),
                    Ingredient(name="tomatoes", quantity=2, unit="whole", notes="medium, chopped"),
                    Ingredient(name="cumin seeds", quantity=1, unit="tsp", notes=None),
                    Ingredient(name="ghee", quantity=1, unit="tbsp", notes=None),
                    Ingredient(name="ginger-garlic paste", quantity=1, unit="tsp", notes=None),
                    Ingredient(name="green chilies", quantity=2, unit="whole", notes="slitlit")
                ],
                instructions=format_instructions_markdown([
                    "Rinse dal thoroughly and pressure cook with 2 cups water and 1/4 tsp turmeric for 15 minutes.",
                    "While dal cooks, knead whole wheat flour with water to make soft dough for roti. Let rest.",
                    "Heat ghee in a pan. Add cumin seeds and let them crackle.",
                    "Add ginger-garlic paste and green chilies. Sauté for 1 minute.",
                    "Add chopped tomatoes and cook until they turn mushy, about 5 minutes.",
                    "Pour the cooked dal into the tadka (tempering). Mix well and simmer for 5 minutes.",
                    "Roll out rotis and cook on hot tawa until puffed and lightly charred.",
                    "Serve hot dal with fresh rotis. Garnish with cilantro and a dollop of ghee."
                ]),
                image_url=generate_recipe_image("Dal Tadka with Roti", "Yellow lentil curry with flatbread"),
                cuisine="Indian",
                difficulty="medium",
                tags=["traditional", "comfort-food", "lentils", "homemade"]
            ),
            Recipe(
                title="Masala Oats with Vegetables",
                description="Savory Indian-spiced oats loaded with colorful vegetables and nuts",
                prep_time="5 mins",
                cook_time="15 mins",
                servings=1,
                macros={
                    "protein_g": target_macros["protein_g"] * 0.7,
                    "carbs_g": target_macros["carbs_g"],
                    "fat_g": target_macros["fat_g"] * 0.8,
                    "calories": target_macros["calories"] * 0.85,
                    "fiber_g": 9.0
                },
                ingredients=[
                    Ingredient(name="rolled oats", quantity=0.75, unit="cup", notes=None),
                    Ingredient(name="mixed vegetables", quantity=1, unit="cup", notes="carrots, peas, beans"),
                    Ingredient(name="onions", quantity=0.5, unit="whole", notes="medium, chopped"),
                    Ingredient(name="curry leaves", quantity=8, unit="whole", notes=None),
                    Ingredient(name="mustard seeds", quantity=0.5, unit="tsp", notes=None),
                    Ingredient(name="cashews", quantity=10, unit="whole", notes="chopped"),
                    Ingredient(name="lemon juice", quantity=1, unit="tbsp", notes=None)
                ],
                instructions=format_instructions_markdown([
                    "Heat oil in a pan and add mustard seeds. Let them splutter.",
                    "Add curry leaves and cashews. Sauté until cashews turn golden.",
                    "Add chopped onions and sauté until translucent.",
                    "Add mixed vegetables and cook for 5 minutes until tender.",
                    "Add rolled oats and 1.5 cups water. Stir well.",
                    "Cover and cook for 5-7 minutes until oats are soft and water is absorbed.",
                    "Add lemon juice, salt, and garnish with cilantro. Serve hot."
                ]),
                image_url=generate_recipe_image("Masala Oats with Vegetables", "Savory spiced oats"),
                cuisine="Indian",
                difficulty="easy",
                tags=["quick", "savory", "oats", "breakfast"]
            ),
            Recipe(
                title="Moong Dal Cheela (Lentil Pancakes)",
                description="Protein-rich savory pancakes made from green lentils with Indian spices",
                prep_time="20 mins (soaking)",
                cook_time="20 mins",
                servings=1,
                macros={
                    "protein_g": target_macros["protein_g"] * 1.1,
                    "carbs_g": target_macros["carbs_g"] * 0.85,
                    "fat_g": target_macros["fat_g"],
                    "calories": target_macros["calories"] * 0.9,
                    "fiber_g": 7.0
                },
                ingredients=[
                    Ingredient(name="moong dal", quantity=0.5, unit="cup", notes="yellow split lentils, soaked"),
                    Ingredient(name="ginger", quantity=1, unit="inch", notes="grated"),
                    Ingredient(name="green chili", quantity=1, unit="whole", notes="chopped"),
                    Ingredient(name="cumin seeds", quantity=0.5, unit="tsp", notes=None),
                    Ingredient(name="onions", quantity=0.25, unit="cup", notes="finely chopped"),
                    Ingredient(name="tomatoes", quantity=0.25, unit="cup", notes="finely chopped"),
                    Ingredient(name="cilantro", quantity=2, unit="tbsp", notes="chopped")
                ],
                instructions=format_instructions_markdown([
                    "Soak moong dal in water for 2-3 hours or overnight. Drain well.",
                    "Blend soaked dal with ginger, green chili, and a little water to make smooth batter.",
                    "Add cumin seeds, chopped onions, tomatoes, and cilantro to the batter. Mix well.",
                    "Heat a non-stick pan and grease lightly with oil.",
                    "Pour a ladleful of batter and spread in a circular motion to make a thin pancake.",
                    "Cook on medium heat for 2-3 minutes until golden. Flip and cook the other side.",
                    "Serve hot with green chutney or yogurt."
                ]),
                image_url=generate_recipe_image("Moong Dal Cheela", "Lentil pancakes"),
                cuisine="Indian",
                difficulty="easy",
                tags=["protein-rich", "savory-pancakes", "lentils", "breakfast"]
            )
        ]
    else:
        # Generic healthy meal options  
        recipes = [
            Recipe(
                title=f"Healthy {cuisine.capitalize()} {meal_type.capitalize()}",
                description=f"Nutritious and balanced {cuisine} style {meal_type} with protein, vegetables, and whole grains",
                prep_time="10 mins",
                cook_time=preferences.get("cook_time", "30 mins"),
                servings=1,
                macros=target_macros,
                ingredients=[
                    Ingredient(name="protein source", quantity=200, unit="g", notes="chicken/tofu/fish"),
                    Ingredient(name="mixed vegetables", quantity=2, unit="cup", notes="seasonal"),
                    Ingredient(name="whole grains", quantity=1, unit="cup", notes="cooked")
                ],
                instructions=format_instructions_markdown([
                    "Prepare your chosen protein source according to your preference.",
                    "Chop and cook vegetables until tender-crisp.",
                    "Cook whole grains according to package directions.",
                    "Combine all components in a bowl.",
                    "Season with herbs and spices to taste. Serve warm."
                ]),
                image_url=generate_recipe_image(f"{cuisine} {meal_type}", "healthy balanced meal"),
                cuisine=cuisine,
                difficulty="medium",
                tags=["balanced", "customizable"]
            )
        ]
    
    return recipes[:5]  # Return up to 5 recipes


@recipe_agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup handler"""
    log_agent_message("RecipeAgent", "🚀 RecipeAgent started and ready!")
    log_agent_message("RecipeAgent", "📡 Chat Protocol v0.3.0 enabled for ASI:One")
    logger.info(f"Agent address: {ctx.agent.address}")


@recipe_agent.on_message(model=RecipeRequest)
async def handle_recipe_request(ctx: Context, sender: str, msg: RecipeRequest):
    """
    Main message handler for RecipeAgent.
    Compatible with ASI:One Chat Protocol v0.3.0.
    Uses Claude API as backbone LLM.
    """
    log_agent_message("RecipeAgent", "📨 Received recipe generation request")
    
    tools_called = ["handle_recipe_request"]
    
    try:
        # Generate recipes using Claude API or mock data
        recipes, generation_tools = generate_recipes_with_claude(msg)
        tools_called.extend(generation_tools)
        
        response = RecipeResponse(
            recipes=recipes,
            message=f"Here are {len(recipes)} personalized recipe options for you!",
            next_action="select_recipe",
            tools_called=tools_called,
            llm_provider="claude" if os.getenv("ANTHROPIC_API_KEY") else "mock"
        )
        
        log_agent_message("RecipeAgent", f"✅ Generated {len(recipes)} recipes")
        log_agent_message("RecipeAgent", f"🔧 Tools called: {', '.join(tools_called)}")
        
        # Send response back
        await ctx.send(sender, response)
        
    except Exception as e:
        logger.error(f"Error generating recipes: {e}")
        tools_called.append("error_handler")
        error_response = RecipeResponse(
            recipes=[],
            message=f"Sorry, I encountered an error: {str(e)}",
            next_action="retry",
            tools_called=tools_called,
            llm_provider="error"
        )
        await ctx.send(sender, error_response)


@recipe_protocol.on_message(model=RecipeRequest)
async def handle_recipe_protocol_message(ctx: Context, sender: str, msg: RecipeRequest):
    """
    Chat Protocol v0.3.0 handler for ASI:One compatibility.
    Generates recipes based on structured requests from other agents.
    This is the official protocol handler for Agentverse discovery.
    Uses Claude API as backbone LLM.
    """
    ctx.logger.info(f"[Chat Protocol v0.3.0] Received recipe request from {sender}")
    log_agent_message("RecipeAgent", f"[Protocol] Generating recipes for {sender}")
    
    tools_called = ["handle_recipe_protocol_message"]
    
    try:
        # Generate recipes using Claude API or mock data
        recipes, generation_tools = generate_recipes_with_claude(msg)
        tools_called.extend(generation_tools)
        
        response = RecipeResponse(
            recipes=recipes,
            message=f"Here are {len(recipes)} personalized recipe options for you!",
            next_action="select_recipe",
            tools_called=tools_called,
            llm_provider="claude" if os.getenv("ANTHROPIC_API_KEY") else "mock"
        )
        
        ctx.logger.info(f"[Chat Protocol v0.3.0] Generated {len(recipes)} recipes, sending to {sender}")
        ctx.logger.info(f"[Chat Protocol v0.3.0] Tools called: {', '.join(tools_called)}")
        log_agent_message("RecipeAgent", f"✅ [Protocol] Sent {len(recipes)} recipes to {sender}")
        
        # Send response back
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"[Chat Protocol v0.3.0] Error generating recipes: {e}")
        logger.error(f"Error generating recipes: {e}")
        tools_called.append("error_handler")
        error_response = RecipeResponse(
            recipes=[],
            message=f"Sorry, I encountered an error: {str(e)}",
            next_action="retry",
            tools_called=tools_called,
            llm_provider="error"
        )
        await ctx.send(sender, error_response)


# Include the Chat Protocol v0.3.0 for ASI:One and Agentverse
recipe_agent.include(recipe_protocol)


def generate_recipes(recipe_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper for recipe generation.
    Used by FastAPI endpoints.
    Uses Claude API as backbone LLM with tool tracking.
    """
    tools_called = ["generate_recipes"]
    
    request = RecipeRequest(**recipe_request)
    recipes, generation_tools = generate_recipes_with_claude(request)
    tools_called.extend(generation_tools)
    
    return {
        "agent": "RecipeAgent",
        "recipes": [recipe.model_dump() for recipe in recipes],
        "message": f"Here are {len(recipes)} personalized recipe options for you!",
        "next_action": "select_recipe",
        "tools_called": tools_called,
        "llm_provider": "claude" if os.getenv("ANTHROPIC_API_KEY") else "mock"
    }


if __name__ == "__main__":
    log_agent_message("RecipeAgent", "Starting RecipeAgent...")
    recipe_agent.run()

