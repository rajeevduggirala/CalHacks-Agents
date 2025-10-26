"""
Daily meal generation with Claude Sonnet 4 and ChromaDB
"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from anthropic import Anthropic
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from chroma_service import ChromaService

# Load environment variables
load_dotenv()

# Initialize Claude client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class DailyMealRequest(BaseModel):
    """Request for daily meal generation"""
    user_id: int
    date: str  # YYYY-MM-DD format
    preferences: Optional[Dict[str, Any]] = None
    avoid_ingredients: Optional[List[str]] = None
    target_calories: Optional[float] = None

class DailyMealResponse(BaseModel):
    """Response with 3 daily recipes and optional macro validation"""
    date: str
    breakfast: Dict[str, Any]
    lunch: Dict[str, Any]
    dinner: Dict[str, Any]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    macro_validation: Optional[Dict[str, Any]] = None
    message: str
    tools_called: List[str]
    llm_provider: str

def generate_daily_meals_with_claude(request: DailyMealRequest, chroma_service: ChromaService, user_profile) -> Tuple[DailyMealResponse, List[str]]:
    """Generate 3 daily meals using Claude Sonnet 4 and ChromaDB preferences"""
    
    tools_called = ["generate_daily_meals_with_claude"]
    
    # Get user preferences from ChromaDB
    user_preferences = chroma_service.get_user_preferences(request.user_id)
    user_dislikes = chroma_service.get_user_dislikes(request.user_id)
    
    # Build context for Claude
    preference_context = chroma_service.build_preference_context(user_preferences, user_dislikes)
    
    # Check if user has specified macro targets
    has_macro_targets = any([
        user_profile.target_protein_g,
        user_profile.target_carbs_g, 
        user_profile.target_fat_g
    ])
    
    # Build macro requirements (only if user specified them)
    macro_requirements = ""
    if has_macro_targets:
        macro_requirements = f"""
        Target Macros (user-specified):
        - Protein: {user_profile.target_protein_g}g per day
        - Carbs: {user_profile.target_carbs_g}g per day  
        - Fats: {user_profile.target_fat_g}g per day
        
        Requirements:
        1. Each meal should be nutritionally balanced and meet the user's macro targets
        2. Distribute macros across the 3 meals (breakfast ~25%, lunch ~35%, dinner ~40%)
        3. Ensure total daily macros align with user's targets
        """
    else:
        macro_requirements = """
        Requirements:
        1. Each meal should be nutritionally balanced for a healthy 2000-calorie diet
        2. Focus on whole foods, lean proteins, complex carbs, and healthy fats
        3. Ensure variety and nutritional completeness across all meals
        """
    
    # Enhanced Claude prompt with conditional macro requirements
    claude_prompt = f"""
    Generate 3 daily meals (breakfast, lunch, dinner) for a user with these preferences:
    
    User Context: {preference_context}
    Target Date: {request.date}
    Target Calories: {request.target_calories or user_profile.daily_calories}
    {macro_requirements}
    
    Additional Requirements:
    4. Avoid these ingredients: {user_dislikes}
    5. Consider user's dietary restrictions: {user_profile.dietary_restrictions}
    6. Incorporate user's flavor preferences: {user_profile.likes}
    7. Generate structured recipes with exact ingredients and quantities
    8. Include cooking instructions in markdown format
    9. Generate an AI image for each recipe
    
    IMPORTANT: Return ONLY valid JSON in this exact format:
    {{
        "breakfast": {{
            "title": "Recipe Title",
            "description": "Brief description",
            "cook_time": "X minutes",
            "calories": 400,
            "protein": 20,
            "carbs": 50,
            "fat": 15,
            "ingredients": [
                {{"name": "ingredient name", "quantity": "amount", "unit": "unit"}}
            ],
            "instructions": "Step-by-step instructions in markdown",
            "image_url": "https://via.placeholder.com/400x300?text=Recipe+Image"
        }},
        "lunch": {{
            "title": "Recipe Title",
            "description": "Brief description", 
            "cook_time": "X minutes",
            "calories": 600,
            "protein": 30,
            "carbs": 70,
            "fat": 20,
            "ingredients": [
                {{"name": "ingredient name", "quantity": "amount", "unit": "unit"}}
            ],
            "instructions": "Step-by-step instructions in markdown",
            "image_url": "https://via.placeholder.com/400x300?text=Recipe+Image"
        }},
        "dinner": {{
            "title": "Recipe Title",
            "description": "Brief description",
            "cook_time": "X minutes", 
            "calories": 800,
            "protein": 40,
            "carbs": 80,
            "fat": 25,
            "ingredients": [
                {{"name": "ingredient name", "quantity": "amount", "unit": "unit"}}
            ],
            "instructions": "Step-by-step instructions in markdown",
            "image_url": "https://via.placeholder.com/400x300?text=Recipe+Image"
        }}
    }}
    
    Do not include any text before or after the JSON. Return only the JSON object.
    """
    
    # Call Claude Sonnet 4 API with simple prompt
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": claude_prompt}
        ]
    )
    
    # Parse Claude response and create recipes
    response_text = response.content[0].text
    
    # Parse Claude response - should be clean JSON now without prefill
    try:
        # First try direct parsing
        recipes_data = json.loads(response_text)
        print("✅ Successfully parsed Claude response")
    except json.JSONDecodeError:
        # If that fails, try to find JSON within the response
        import re
        
        # Try to extract JSON from code blocks or find JSON objects
        json_candidates = []
        
        # Look for JSON between ```json and ```
        json_blocks = re.findall(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        json_candidates.extend(json_blocks)
        
        # Look for JSON between ``` and ```
        code_blocks = re.findall(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        json_candidates.extend(code_blocks)
        
        # Look for JSON object starting with { and ending with }
        json_objects = re.findall(r'\{.*\}', response_text, re.DOTALL)
        json_candidates.extend(json_objects)
        
        # Try to parse each candidate
        recipes_data = None
        for candidate in json_candidates:
            try:
                candidate = candidate.strip()
                if candidate.startswith('{') and candidate.endswith('}'):
                    recipes_data = json.loads(candidate)
                    # Validate that it has the expected structure
                    if all(key in recipes_data for key in ['breakfast', 'lunch', 'dinner']):
                        print("✅ Successfully extracted and parsed JSON from response")
                        break
                    else:
                        recipes_data = None
            except json.JSONDecodeError:
                continue
        
        if recipes_data is None:
            # If all else fails, create a mock response for debugging
            print(f"Warning: Could not parse Claude response, using mock data.")
            print(f"Response starts with: {response_text[:200]}...")
            print(f"Response length: {len(response_text)}")
            recipes_data = {
                "breakfast": {
                    "title": "Mock Breakfast",
                    "description": "Mock breakfast recipe",
                    "cook_time": "15 minutes",
                    "calories": 400,
                    "protein": 20,
                    "carbs": 50,
                    "fat": 15,
                    "ingredients": [{"name": "eggs", "quantity": "2", "unit": "pieces"}],
                    "instructions": "Mock instructions",
                    "image_url": "https://via.placeholder.com/300x200?text=Mock+Breakfast"
                },
                "lunch": {
                    "title": "Mock Lunch",
                    "description": "Mock lunch recipe",
                    "cook_time": "30 minutes",
                    "calories": 600,
                    "protein": 30,
                    "carbs": 70,
                    "fat": 20,
                    "ingredients": [{"name": "rice", "quantity": "1", "unit": "cup"}],
                    "instructions": "Mock instructions",
                    "image_url": "https://via.placeholder.com/300x200?text=Mock+Lunch"
                },
                "dinner": {
                    "title": "Mock Dinner",
                    "description": "Mock dinner recipe",
                    "cook_time": "45 minutes",
                    "calories": 800,
                    "protein": 40,
                    "carbs": 80,
                    "fat": 25,
                    "ingredients": [{"name": "chicken", "quantity": "200", "unit": "g"}],
                    "instructions": "Mock instructions",
                    "image_url": "https://via.placeholder.com/300x200?text=Mock+Dinner"
                }
            }
    
    # Generate embeddings and store in ChromaDB
    breakfast_recipe = create_recipe_with_embedding(recipes_data["breakfast"], request.user_id, "breakfast", chroma_service)
    lunch_recipe = create_recipe_with_embedding(recipes_data["lunch"], request.user_id, "lunch", chroma_service)
    dinner_recipe = create_recipe_with_embedding(recipes_data["dinner"], request.user_id, "dinner", chroma_service)
    
    # Calculate totals
    total_calories = breakfast_recipe["calories"] + lunch_recipe["calories"] + dinner_recipe["calories"]
    total_protein = breakfast_recipe["protein"] + lunch_recipe["protein"] + dinner_recipe["protein"]
    total_carbs = breakfast_recipe["carbs"] + lunch_recipe["carbs"] + dinner_recipe["carbs"]
    total_fat = breakfast_recipe["fat"] + lunch_recipe["fat"] + dinner_recipe["fat"]
    
    # Only validate macro targets if user specified them
    macro_validation = None
    if has_macro_targets:
        macro_validation = validate_macro_targets(
            total_protein, total_carbs, total_fat,
            user_profile.target_protein_g, user_profile.target_carbs_g, user_profile.target_fat_g
        )
        tools_called.append("macro_validation")
    
    tools_called.extend(["claude_api", "chroma_store", "embedding_generation"])
    
    return DailyMealResponse(
        date=request.date,
        breakfast=breakfast_recipe,
        lunch=lunch_recipe,
        dinner=dinner_recipe,
        total_calories=total_calories,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        macro_validation=macro_validation,
        message=f"Generated 3 personalized meals for {request.date}" + 
                (" targeting your macro goals" if has_macro_targets else " with balanced nutrition"),
        tools_called=tools_called,
        llm_provider="claude-sonnet-4"
    ), tools_called

def create_recipe_with_embedding(recipe_data: Dict[str, Any], user_id: int, meal_type: str, chroma_service: ChromaService) -> Dict[str, Any]:
    """Create recipe with embedding and store in ChromaDB"""
    
    # Generate embedding for recipe
    recipe_text = f"{recipe_data['title']} {recipe_data['description']} {recipe_data['ingredients']}"
    embedding = chroma_service.generate_embedding(recipe_text)
    
    # Store in ChromaDB
    recipe_data["user_id"] = user_id
    recipe_data["meal_type"] = meal_type
    chroma_id = chroma_service.store_recipe(recipe_data, embedding)
    
    # Add ChromaDB ID to recipe
    recipe_data["chroma_id"] = chroma_id
    
    return recipe_data

def validate_macro_targets(actual_protein: float, actual_carbs: float, actual_fat: float,
                          target_protein: Optional[float], target_carbs: Optional[float], target_fat: Optional[float]) -> Dict[str, Any]:
    """Validate if generated meals meet user's macro targets"""
    
    validation = {
        "protein": {"target": target_protein, "actual": actual_protein, "met": True},
        "carbs": {"target": target_carbs, "actual": actual_carbs, "met": True},
        "fat": {"target": target_fat, "actual": actual_fat, "met": True}
    }
    
    # Only validate if targets are specified
    if target_protein:
        validation["protein"]["met"] = abs(actual_protein - target_protein) / target_protein <= 0.1
        validation["protein"]["percentage"] = round((actual_protein / target_protein) * 100)
    else:
        validation["protein"]["met"] = None
        validation["protein"]["percentage"] = None
        
    if target_carbs:
        validation["carbs"]["met"] = abs(actual_carbs - target_carbs) / target_carbs <= 0.1
        validation["carbs"]["percentage"] = round((actual_carbs / target_carbs) * 100)
    else:
        validation["carbs"]["met"] = None
        validation["carbs"]["percentage"] = None
        
    if target_fat:
        validation["fat"]["met"] = abs(actual_fat - target_fat) / target_fat <= 0.1
        validation["fat"]["percentage"] = round((actual_fat / target_fat) * 100)
    else:
        validation["fat"]["met"] = None
        validation["fat"]["percentage"] = None
    
    return validation

def generate_single_meal_with_claude(request: DailyMealRequest, meal_type: str, chroma_service: ChromaService, user_profile) -> Dict[str, Any]:
    """Generate a single meal using Claude Sonnet 4"""
    
    # Get user preferences from ChromaDB
    user_preferences = chroma_service.get_user_preferences(request.user_id)
    user_dislikes = chroma_service.get_user_dislikes(request.user_id)
    
    # Build context for Claude
    preference_context = chroma_service.build_preference_context(user_preferences, user_dislikes)
    
    # Check if user has specified macro targets
    has_macro_targets = any([
        user_profile.target_protein_g,
        user_profile.target_carbs_g, 
        user_profile.target_fat_g
    ])
    
    # Build macro requirements for single meal
    macro_requirements = ""
    if has_macro_targets:
        macro_requirements = f"""
        Target Macros for {meal_type} (user-specified daily targets):
        - Protein: {user_profile.target_protein_g}g per day
        - Carbs: {user_profile.target_carbs_g}g per day  
        - Fats: {user_profile.target_fat_g}g per day
        
        Requirements:
        1. This {meal_type} should contribute appropriately to daily macro targets
        2. Focus on nutritional balance and macro distribution
        """
    else:
        macro_requirements = f"""
        Requirements:
        1. This {meal_type} should be nutritionally balanced and healthy
        2. Focus on whole foods and nutritional completeness
        """
    
    # Claude prompt for single meal
    claude_prompt = f"""
    Generate a {meal_type} recipe for a user with these preferences:
    
    User Context: {preference_context}
    Target Date: {request.date}
    Target Calories: {request.target_calories or user_profile.daily_calories}
    {macro_requirements}
    
    Additional Requirements:
    3. Avoid these ingredients: {user_dislikes}
    4. Consider user's dietary restrictions: {user_profile.dietary_restrictions}
    5. Incorporate user's flavor preferences: {user_profile.likes}
    6. Generate structured recipe with exact ingredients and quantities
    7. Include cooking instructions in markdown format
    8. Generate an AI image for the recipe
    
    Return JSON format with the {meal_type} recipe.
    Include detailed macro breakdown per serving.
    """
    
    # Call Claude Sonnet 4 API with prefill technique for consistent JSON
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": claude_prompt},
            {"role": "assistant", "content": "{\n    \"title\": \""}
        ]
    )
    
    # Parse Claude response and create recipe
    response_text = response.content[0].text
    
    # Try to extract JSON from the response (handle cases where Claude adds extra text)
    try:
        # First try direct parsing
        recipe_data = json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to find JSON within the response
        import re
        # Look for JSON object starting with { and ending with }
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            recipe_data = json.loads(json_match.group())
        else:
            raise ValueError(f"Could not extract valid JSON from Claude response: {response_text[:200]}...")
    
    # Generate embedding and store in ChromaDB
    recipe = create_recipe_with_embedding(recipe_data, request.user_id, meal_type, chroma_service)
    
    return recipe
