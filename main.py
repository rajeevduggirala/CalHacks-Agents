"""
Agentic Grocery - FastAPI Backend
Multi-agent system for food recommendation and grocery automation
Integrates Fetch.ai's uAgents with FastAPI for ASI:One compatibility
Includes authentication, user management, and SQLite database
"""

import os
import sys
import json
import warnings
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

# Suppress PyTorch deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Import agent modules
from agents.recipe_agent.agent import generate_recipes
from agents.grocery_agent.agent import generate_grocery_list
from agents.recipe_agent.daily_meals import (
    generate_daily_meals_with_claude, 
    generate_single_meal_with_claude,
    DailyMealRequest,
    DailyMealResponse
)
from chroma_service import ChromaService
from utils.logger import setup_logger, log_api_call

# Import database and auth
from database import (
    get_db, init_db, create_user, get_user_by_email, get_user_by_username,
    create_user_profile, save_recipe as db_save_recipe,
    create_grocery_list as db_create_grocery_list, log_meal as db_log_meal,
    create_daily_meal_plan, get_daily_meal_plan, create_user_preference,
    User, UserProfile, Recipe, GroceryList, MealHistory, DailyMealPlan, UserPreference
)
from auth import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("AgenticGrocery")

# Initialize ChromaDB service
chroma_service = ChromaService()

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    logger.info("🚀 Starting Agentic Grocery API...")
    
    # Initialize database
    init_db()
    logger.info("✅ Database initialized")
    
    logger.info("✅ All agents initialized and ready")
    yield
    logger.info("👋 Shutting down Agentic Grocery API...")


# Initialize FastAPI app
app = FastAPI(
    title="Agentic Grocery API",
    description="Multi-agent system for food recommendations and grocery automation using Fetch.ai uAgents",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses


class RecipeRequest(BaseModel):
    """Recipe endpoint request model"""
    user_profile: Dict[str, Any] = Field(..., description="User profile data")
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class GroceryRequest(BaseModel):
    """Grocery endpoint request model"""
    recipe: Dict[str, Any] = Field(..., description="Selected recipe")
    user_id: str = Field(default="raj", description="User identifier")
    store_preference: str = Field(default="Kroger", description="Preferred store (Kroger API supported)")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    version: str
    agents: Dict[str, str]


# Authentication Models
class MacrosOptional(BaseModel):
    """Optional macros for user"""
    protein: Optional[float] = Field(None, description="Daily protein target in grams")
    carbs: Optional[float] = Field(None, description="Daily carbs target in grams")
    fats: Optional[float] = Field(None, description="Daily fats target in grams")


class UserRegister(BaseModel):
    """User registration model with detailed food preferences"""
    # Account credentials
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, description="Password for login")
    
    # Personal information
    name: str = Field(..., min_length=1, description="Full name")
    
    # Dietary information (required)
    daily_calories: float = Field(..., gt=0, description="Daily calorie target")
    dietary_restrictions: List[str] = Field(
        ..., 
        description="Dietary restrictions including allergies, diet type (vegetarian, vegan, etc.)",
        example=["vegetarian", "gluten-free", "no nuts"]
    )
    likes: List[str] = Field(
        ..., 
        description="Cuisines and flavor profiles (e.g., 'indian', 'spicy', 'sweet', 'savory')",
        example=["indian", "spicy", "savory", "grilled"]
    )
    
    # Optional information
    additional_information: Optional[str] = Field(
        None, 
        description="Additional free-form text about food preferences",
        example="I prefer low-carb meals after 6pm. Love garlic in everything."
    )
    macros: Optional[MacrosOptional] = Field(
        None,
        description="Optional macro targets (protein, carbs, fats)"
    )


class UserLogin(BaseModel):
    """User login model"""
    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    user: Dict[str, Any]


class UserProfileUpdate(BaseModel):
    """User profile update model"""
    # Dietary information
    daily_calories: Optional[float] = Field(None, gt=0, description="Daily calorie target")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions including allergies")
    likes: Optional[List[str]] = Field(None, description="Cuisines and flavor profiles")
    additional_information: Optional[str] = Field(None, description="Additional food preferences")
    
    # Optional macros
    target_protein_g: Optional[float] = Field(None, ge=0, description="Daily protein target in grams")
    target_carbs_g: Optional[float] = Field(None, ge=0, description="Daily carbs target in grams")
    target_fat_g: Optional[float] = Field(None, ge=0, description="Daily fats target in grams")


class MealFeedbackRequest(BaseModel):
    """Feedback on daily meals"""
    date: str
    breakfast_rating: Optional[int] = Field(None, ge=1, le=5)
    lunch_rating: Optional[int] = Field(None, ge=1, le=5)
    dinner_rating: Optional[int] = Field(None, ge=1, le=5)
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    disliked_ingredients: Optional[List[str]] = None
    liked_ingredients: Optional[List[str]] = None


class RegenerateMealRequest(BaseModel):
    """Request to regenerate a specific meal"""
    date: str
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner)$")


class RecipeIngredient(BaseModel):
    """Recipe ingredient model"""
    name: str = Field(..., description="Ingredient name")
    quantity: float = Field(..., description="Quantity needed")
    unit: str = Field(..., description="Unit of measurement")
    notes: Optional[str] = Field(None, description="Additional notes")


class RecipeForGrocery(BaseModel):
    """Recipe model for grocery list generation"""
    title: str = Field(..., description="Recipe title")
    ingredients: List[RecipeIngredient] = Field(..., description="List of ingredients")
    servings: Optional[int] = Field(1, description="Number of servings")
    description: Optional[str] = Field(None, description="Recipe description")


# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Agentic Grocery API",
        "version": "0.3.0",
        "description": "Multi-agent system for food recommendations and grocery automation",
        "features": ["Multi-Agent AI", "Claude Recipes", "Kroger Integration", "User Authentication"],
        "agents": ["RecipeAgent", "GroceryAgent"],
        "docs": "/docs",
        "health": "/health",
        "auth": {
            "register": "/auth/register",
            "login": "/auth/login"
        }
    }


# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/auth/register", response_model=TokenResponse, tags=["Authentication"])
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account with detailed food preferences
    
    Required fields:
    - email, username, password: Account credentials
    - name: Full name
    - daily_calories: Daily calorie target
    - dietary_restrictions: List including allergies, diet type (e.g., ['vegetarian', 'no nuts'])
    - likes: Cuisines and flavor profiles (e.g., ['indian', 'spicy', 'savory'])
    
    Optional fields:
    - additional_information: Free-form text about food preferences
    - macros: {protein, carbs, fats} - Optional macro targets
    
    Returns JWT token for immediate authentication with user profile.
    """
    log_api_call("/auth/register", "started")
    
    # Check if user exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user with name
    user = User(
        email=user_data.email,
        username=user_data.username,
        name=user_data.name,
        hashed_password=User.hash_password(user_data.password)
    )
    db.add(user)
    db.flush()  # Get user ID before creating profile
    
    # Create user profile with detailed food preferences
    profile = UserProfile(
        user_id=user.id,
        # Required dietary information
        daily_calories=user_data.daily_calories,
        dietary_restrictions=user_data.dietary_restrictions,
        likes=user_data.likes,
        additional_information=user_data.additional_information,
        # Optional macros
        target_protein_g=user_data.macros.protein if user_data.macros else None,
        target_carbs_g=user_data.macros.carbs if user_data.macros else None,
        target_fat_g=user_data.macros.fats if user_data.macros else None
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    log_api_call("/auth/register", "completed")
    logger.info(f"New user registered: {user.username} ({user.name})")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "daily_calories": user_data.daily_calories,
            "dietary_restrictions": user_data.dietary_restrictions,
            "likes": user_data.likes
        }
    }


@app.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT token
    
    Authenticates user with email and password.
    Returns JWT token valid for 7 days.
    """
    log_api_call("/auth/login", "started")
    
    user = get_user_by_email(db, credentials.email)
    
    if not user or not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    log_api_call("/auth/login", "completed")
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "name": user.name
        }
    }


# ==================== USER PROFILE ENDPOINTS ====================

@app.get("/profile", tags=["User Profile"])
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile
    
    Requires authentication. Returns user info and detailed dietary profile including:
    - Name, daily calories, dietary restrictions, likes, additional info
    - Optional macros and physical stats
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    profile_data = None
    if profile:
        profile_data = {
            "daily_calories": profile.daily_calories,
            "dietary_restrictions": profile.dietary_restrictions,
            "likes": profile.likes,
            "additional_information": profile.additional_information,
            "macros": {
                "protein": profile.target_protein_g,
                "carbs": profile.target_carbs_g,
                "fats": profile.target_fat_g
            } if profile.target_protein_g or profile.target_carbs_g or profile.target_fat_g else None
        }
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "name": current_user.name,
            "created_at": current_user.created_at
        },
        "profile": profile_data
    }


@app.put("/profile", tags=["User Profile"])
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile
    
    Updates dietary preferences, physical stats, and fitness goals.
    Only updates fields that are provided.
    """
    # Filter out None values
    update_data = {k: v for k, v in profile_data.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update"
        )
    
    profile = create_user_profile(db, current_user.id, update_data)
    
    logger.info(f"Profile updated for user: {current_user.username}")
    
    return {"message": "Profile updated successfully", "profile": profile}


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring
    Returns status of all agents and system
    """
    log_api_call("/health", "started")
    
    try:
        health_status = HealthResponse(
            status="healthy",
            message="All systems operational",
            version="0.3.0",
            agents={
                "RecipeAgent": "operational",
                "GroceryAgent": "operational"
            }
        )
        log_api_call("/health", "completed")
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@app.post("/recipe", tags=["Agents"])
async def recipe_endpoint(
    request: RecipeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recipe endpoint - generates personalized recipes
    
    **Requires Authentication**
    
    RecipeAgent creates 2-3 meal options based on authenticated user's profile and preferences.
    Uses Claude AI for intelligent recipe generation.
    Uses structured data compatible with Chat Protocol v0.3.0
    
    Args:
        request: RecipeRequest with preferences (user_profile optional, will use authenticated user's profile)
        current_user: Authenticated user (from JWT token)
    
    Returns:
        List of generated recipes with macros and instructions
    """
    log_api_call("/recipe", "started")
    logger.info(f"Generating recipes for user: {current_user.username}")
    
    try:
        # Get user profile from database
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        # Use provided user_profile or construct from database
        if not request.user_profile and profile:
            user_profile_dict = {
                "height_cm": profile.height_cm,
                "weight_kg": profile.weight_kg,
                "goal": profile.goal,
                "diet": profile.diet,
                "workout_frequency": profile.workout_frequency,
                "likes": profile.likes or [],
                "dislikes": profile.dislikes or [],
                "allergies": profile.allergies or [],
                "target_macros": {
                    "protein_g": profile.target_protein_g or 140,
                    "carbs_g": profile.target_carbs_g or 200,
                    "fat_g": profile.target_fat_g or 50,
                    "calories": profile.target_calories or 1800
                }
            }
        else:
            user_profile_dict = request.user_profile or {}
        
        # Generate recipes through RecipeAgent
        recipe_request_dict = {
            "user_profile": user_profile_dict,
            "preferences": request.preferences,
            "context": request.context
        }
        
        response = generate_recipes(recipe_request_dict)
        
        log_api_call("/recipe", "completed")
        logger.info(f"Generated {len(response.get('recipes', []))} recipes for {current_user.username}")
        return response
        
    except Exception as e:
        logger.error(f"Recipe endpoint error: {e}")
        log_api_call("/recipe", "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recipes: {str(e)}"
        )


@app.post("/grocery", tags=["Agents"])
async def grocery_endpoint(
    request: GroceryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Grocery endpoint - creates grocery list from recipe
    
    **Requires Authentication**
    
    GroceryAgent extracts ingredients and creates formatted list with Kroger prices.
    Automatically saves list to user's account.
    
    Args:
        request: GroceryRequest with selected recipe
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Grocery list with items, quantities, and estimated costs
    """
    log_api_call("/grocery", "started")
    logger.info(f"Creating grocery list for user: {current_user.username}")
    
    try:
        # Generate grocery list through GroceryAgent
        grocery_request_dict = {
            "recipe": request.recipe,
            "user_id": current_user.username,
            "store_preference": request.store_preference
        }
        
        response = generate_grocery_list(grocery_request_dict)
        
        # Save to database
        grocery_list = db_create_grocery_list(db, current_user.id, {
            "name": f"List for {request.recipe.get('title', 'Recipe')}",
            "store": response["store"],
            "total_cost": response["total_estimated_cost"],
            "items": response["items"]
        })
        
        log_api_call("/grocery", "completed")
        logger.info(f"Created and saved list with {len(response.get('items', []))} items")
        
        # Return response with database ID
        response["list_id"] = grocery_list.id
        return response
        
    except Exception as e:
        logger.error(f"Grocery endpoint error: {e}")
        log_api_call("/grocery", "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating grocery list: {str(e)}"
        )


#==================== DAILY MEAL PLANNING ENDPOINTS ====================

@app.post("/daily-meals/generate", tags=["Daily Meals"])
async def generate_daily_meals(
    day: str,  # Day name: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate 3 daily meals (breakfast, lunch, dinner) with macro targets"""
    
    # Get user profile with macro targets
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Generate daily meals with macro consideration
    request = DailyMealRequest(
        user_id=current_user.id,
        date=day,  # Use day name directly
        target_calories=profile.daily_calories
    )
    
    response, tools_called = generate_daily_meals_with_claude(request, chroma_service, profile)
    
    # Save recipes to database
    breakfast_recipe = Recipe(
        user_id=current_user.id,
        title=response.breakfast["title"],
        description=response.breakfast["description"],
        meal_type="breakfast",
        cook_time=response.breakfast["cook_time"],
        prep_time=response.breakfast.get("prep_time", "15 minutes"),
        servings=response.breakfast.get("servings", 1),
        cuisine=response.breakfast.get("cuisine"),
        difficulty=response.breakfast.get("difficulty", "medium"),
        protein_g=response.breakfast["protein"],
        carbs_g=response.breakfast["carbs"],
        fat_g=response.breakfast["fat"],
        calories=response.breakfast["calories"],
        ingredients=response.breakfast["ingredients"],
        instructions=response.breakfast["instructions"],
        image_url=response.breakfast.get("image_url", ""),
        chroma_id=response.breakfast.get("chroma_id", "")
    )
    
    lunch_recipe = Recipe(
        user_id=current_user.id,
        title=response.lunch["title"],
        description=response.lunch["description"],
        meal_type="lunch",
        cook_time=response.lunch["cook_time"],
        prep_time=response.lunch.get("prep_time", "15 minutes"),
        servings=response.lunch.get("servings", 1),
        cuisine=response.lunch.get("cuisine"),
        difficulty=response.lunch.get("difficulty", "medium"),
        protein_g=response.lunch["protein"],
        carbs_g=response.lunch["carbs"],
        fat_g=response.lunch["fat"],
        calories=response.lunch["calories"],
        ingredients=response.lunch["ingredients"],
        instructions=response.lunch["instructions"],
        image_url=response.lunch.get("image_url", ""),
        chroma_id=response.lunch.get("chroma_id", "")
    )
    
    dinner_recipe = Recipe(
        user_id=current_user.id,
        title=response.dinner["title"],
        description=response.dinner["description"],
        meal_type="dinner",
        cook_time=response.dinner["cook_time"],
        prep_time=response.dinner.get("prep_time", "15 minutes"),
        servings=response.dinner.get("servings", 1),
        cuisine=response.dinner.get("cuisine"),
        difficulty=response.dinner.get("difficulty", "medium"),
        protein_g=response.dinner["protein"],
        carbs_g=response.dinner["carbs"],
        fat_g=response.dinner["fat"],
        calories=response.dinner["calories"],
        ingredients=response.dinner["ingredients"],
        instructions=response.dinner["instructions"],
        image_url=response.dinner.get("image_url", ""),
        chroma_id=response.dinner.get("chroma_id", "")
    )
    
    db.add_all([breakfast_recipe, lunch_recipe, dinner_recipe])
    db.flush()  # Get IDs
    
    # Save meal plan (use current date since we're working with day names)
    meal_plan = DailyMealPlan(
        user_id=current_user.id,
        date=datetime.now().date(),
        breakfast_recipe_id=breakfast_recipe.id,
        lunch_recipe_id=lunch_recipe.id,
        dinner_recipe_id=dinner_recipe.id
    )
    db.add(meal_plan)
    db.commit()
    
    return response


@app.post("/daily-meals/generate-by-day", tags=["Daily Meals"])
async def generate_daily_meals_by_day(
    day: str,  # Day name: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate 3 daily meals for a specific day of the week"""
    
    # Validate day name
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day not in valid_days:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid day. Must be one of: {', '.join(valid_days)}"
        )
    
    # Get user profile with macro targets
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Generate daily meals with macro consideration
    request = DailyMealRequest(
        user_id=current_user.id,
        date=day,  # Pass the day name directly
        target_calories=profile.daily_calories
    )
    
    response, tools_called = generate_daily_meals_with_claude(request, chroma_service, profile)
    
    # Save recipes to database
    breakfast_recipe = Recipe(
        user_id=current_user.id,
        title=response.breakfast["title"],
        description=response.breakfast["description"],
        meal_type="breakfast",
        cook_time=response.breakfast["cook_time"],
        prep_time=response.breakfast.get("prep_time", "15 minutes"),
        servings=response.breakfast.get("servings", 1),
        cuisine=response.breakfast.get("cuisine"),
        difficulty=response.breakfast.get("difficulty", "medium"),
        calories=response.breakfast["calories"],
        protein_g=response.breakfast["protein"],
        carbs_g=response.breakfast["carbs"],
        fat_g=response.breakfast["fat"],
        ingredients=json.dumps(response.breakfast["ingredients"]),
        instructions=response.breakfast["instructions"],
        image_url=response.breakfast.get("image_url", ""),
        chroma_id=response.breakfast.get("chroma_id", "")
    )
    
    lunch_recipe = Recipe(
        user_id=current_user.id,
        title=response.lunch["title"],
        description=response.lunch["description"],
        meal_type="lunch",
        cook_time=response.lunch["cook_time"],
        prep_time=response.lunch.get("prep_time", "15 minutes"),
        servings=response.lunch.get("servings", 1),
        cuisine=response.lunch.get("cuisine"),
        difficulty=response.lunch.get("difficulty", "medium"),
        calories=response.lunch["calories"],
        protein_g=response.lunch["protein"],
        carbs_g=response.lunch["carbs"],
        fat_g=response.lunch["fat"],
        ingredients=json.dumps(response.lunch["ingredients"]),
        instructions=response.lunch["instructions"],
        image_url=response.lunch.get("image_url", ""),
        chroma_id=response.lunch.get("chroma_id", "")
    )
    
    dinner_recipe = Recipe(
        user_id=current_user.id,
        title=response.dinner["title"],
        description=response.dinner["description"],
        meal_type="dinner",
        cook_time=response.dinner["cook_time"],
        prep_time=response.dinner.get("prep_time", "15 minutes"),
        servings=response.dinner.get("servings", 1),
        cuisine=response.dinner.get("cuisine"),
        difficulty=response.dinner.get("difficulty", "medium"),
        calories=response.dinner["calories"],
        protein_g=response.dinner["protein"],
        carbs_g=response.dinner["carbs"],
        fat_g=response.dinner["fat"],
        ingredients=json.dumps(response.dinner["ingredients"]),
        instructions=response.dinner["instructions"],
        image_url=response.dinner.get("image_url", ""),
        chroma_id=response.dinner.get("chroma_id", "")
    )
    
    db.add_all([breakfast_recipe, lunch_recipe, dinner_recipe])
    db.commit()
    
    # Create daily meal plan
    daily_plan = DailyMealPlan(
        user_id=current_user.id,
        date=datetime.now().date(),  # Use current date for database
        breakfast_recipe_id=breakfast_recipe.id,
        lunch_recipe_id=lunch_recipe.id,
        dinner_recipe_id=dinner_recipe.id
    )
    
    db.add(daily_plan)
    db.commit()
    
    # Store recipes in ChromaDB for preference learning
    for recipe_data, recipe_obj in [
        (response.breakfast, breakfast_recipe),
        (response.lunch, lunch_recipe),
        (response.dinner, dinner_recipe)
    ]:
        recipe_embedding = chroma_service.generate_embedding(
            f"{recipe_data['title']} {recipe_data['description']} {', '.join([ing['name'] for ing in recipe_data['ingredients']])}"
        )
        
        recipe_data_for_chroma = {
            "user_id": current_user.id,
            "recipe_id": recipe_obj.id,
            "title": recipe_data["title"],
            "description": recipe_data["description"],
            "meal_type": recipe_obj.meal_type,
            "cuisine": recipe_data.get("cuisine", ""),
            "calories": recipe_data["calories"],
            "ingredients": [ing["name"] for ing in recipe_data["ingredients"]]
        }
        
        chroma_id = chroma_service.store_recipe(recipe_data_for_chroma, recipe_embedding)
        recipe_obj.chroma_id = chroma_id
        db.commit()
    
    log_api_call("/daily-meals/generate-by-day", "completed")
    
    return response


@app.post("/daily-meals/regenerate", tags=["Daily Meals"])
async def regenerate_meal(
    request: RegenerateMealRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate a specific meal for the day"""
    
    # Get existing meal plan
    meal_plan = db.query(DailyMealPlan).filter(
        DailyMealPlan.user_id == current_user.id,
        DailyMealPlan.date == datetime.strptime(request.date, "%Y-%m-%d")
    ).first()
    
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Get user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # Generate new recipe for the meal type
    meal_request = DailyMealRequest(
        user_id=current_user.id,
        date=request.date,
        target_calories=profile.daily_calories if profile else 2000
    )
    
    # Generate single meal
    new_recipe_data = generate_single_meal_with_claude(meal_request, request.meal_type, chroma_service, profile)
    
    # Create new recipe in database
    new_recipe = Recipe(
        user_id=current_user.id,
        title=new_recipe_data["title"],
        description=new_recipe_data["description"],
        meal_type=request.meal_type,
        cook_time=new_recipe_data["cook_time"],
        prep_time=new_recipe_data.get("prep_time", "15 minutes"),
        servings=new_recipe_data.get("servings", 1),
        cuisine=new_recipe_data.get("cuisine"),
        difficulty=new_recipe_data.get("difficulty", "medium"),
        protein_g=new_recipe_data["protein"],
        carbs_g=new_recipe_data["carbs"],
        fat_g=new_recipe_data["fat"],
        calories=new_recipe_data["calories"],
        ingredients=new_recipe_data["ingredients"],
        instructions=new_recipe_data["instructions"],
        image_url=new_recipe_data.get("image_url", ""),
        chroma_id=new_recipe_data.get("chroma_id", "")
    )
    
    db.add(new_recipe)
    db.flush()  # Get ID
    
    # Update meal plan
    if request.meal_type == "breakfast":
        meal_plan.breakfast_recipe_id = new_recipe.id
    elif request.meal_type == "lunch":
        meal_plan.lunch_recipe_id = new_recipe.id
    elif request.meal_type == "dinner":
        meal_plan.dinner_recipe_id = new_recipe.id
    
    db.commit()
    
    return {
        "message": f"Regenerated {request.meal_type} for {request.date}",
        "recipe": new_recipe_data
    }

@app.post("/daily-meals/feedback", tags=["Daily Meals"])
async def submit_meal_feedback(
    feedback: MealFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback on daily meals to improve future recommendations"""
    
    # Store feedback in ChromaDB for learning
    preference_data = {
        "user_id": current_user.id,
        "date": feedback.date,
        "feedback": feedback.dict(),
        "preference_type": "feedback"
    }
    
    # Generate embedding and store
    embedding = chroma_service.generate_embedding(json.dumps(preference_data))
    chroma_service.store_user_preference(current_user.id, preference_data, embedding)
    
    # Store individual ingredient preferences
    if feedback.disliked_ingredients:
        for ingredient in feedback.disliked_ingredients:
            pref_data = {
                "user_id": current_user.id,
                "preference_type": "disliked",
                "item_name": ingredient,
                "item_type": "ingredient",
                "context": f"Disliked in meal on {feedback.date}",
                "strength": 1.0
            }
            embedding = chroma_service.generate_embedding(ingredient)
            chroma_service.store_user_preference(current_user.id, pref_data, embedding)
    
    if feedback.liked_ingredients:
        for ingredient in feedback.liked_ingredients:
            pref_data = {
                "user_id": current_user.id,
                "preference_type": "liked",
                "item_name": ingredient,
                "item_type": "ingredient",
                "context": f"Liked in meal on {feedback.date}",
                "strength": 1.0
            }
            embedding = chroma_service.generate_embedding(ingredient)
            chroma_service.store_user_preference(current_user.id, pref_data, embedding)
    
    return {"message": "Feedback recorded for future recommendations"}

@app.get("/daily-meals/{date}", tags=["Daily Meals"])
async def get_daily_meals(
    date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily meal plan for a specific date"""
    
    meal_plan = db.query(DailyMealPlan).filter(
        DailyMealPlan.user_id == current_user.id,
        DailyMealPlan.date == datetime.strptime(date, "%Y-%m-%d")
    ).first()
    
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Get recipes
    breakfast = db.query(Recipe).filter(Recipe.id == meal_plan.breakfast_recipe_id).first()
    lunch = db.query(Recipe).filter(Recipe.id == meal_plan.lunch_recipe_id).first()
    dinner = db.query(Recipe).filter(Recipe.id == meal_plan.dinner_recipe_id).first()
    
    return {
        "date": date,
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner,
        "user_rating": meal_plan.user_rating,
        "notes": meal_plan.notes,
        "is_completed": meal_plan.is_completed
    }

@app.get("/daily-meals", tags=["Daily Meals"])
async def get_user_meal_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 30
):
    """Get user's meal plan history"""
    
    meal_plans = db.query(DailyMealPlan).filter(
        DailyMealPlan.user_id == current_user.id
    ).order_by(DailyMealPlan.date.desc()).limit(limit).all()
    
    return {"meal_plans": meal_plans}


#==================== GROCERY SHOPPING ENDPOINTS ====================

@app.post("/grocery/from-recipe", tags=["Grocery Shopping"])
async def create_grocery_list_from_recipe(
    recipe: RecipeForGrocery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create grocery list from recipe using Kroger API
    
    **Requires Authentication**
    
    Takes a recipe and searches Kroger API for each ingredient to get:
    - Real product names and descriptions
    - Current prices
    - Product images
    - Available quantities
    
    Args:
        recipe: Recipe object with ingredients list
        current_user: Authenticated user
    
    Returns:
        Grocery list with Kroger product details, prices, and images
    """
    log_api_call("/grocery/from-recipe", "started")
    logger.info(f"Creating grocery list from recipe for user: {current_user.username}")
    
    try:
        # Import Kroger API functions from grocery agent
        from agents.grocery_agent.agent import get_kroger_token, search_kroger_product
        
        # Get Kroger API token
        token = get_kroger_token()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kroger API unavailable"
            )
        
        # Extract ingredients from recipe
        ingredients = recipe.ingredients
        if not ingredients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipe must contain ingredients"
            )
        
        grocery_items = []
        total_cost = 0.0
        kroger_items_found = 0
        
        # Search Kroger for each ingredient
        for ingredient in ingredients:
            ingredient_name = ingredient.name
            quantity = ingredient.quantity
            unit = ingredient.unit
            
            if not ingredient_name:
                continue
            
            # Search Kroger API for this ingredient
            kroger_result = search_kroger_product(ingredient_name)
            
            if kroger_result and kroger_result.get("price"):
                # Found on Kroger
                kroger_items_found += 1
                item_cost = float(kroger_result["price"]) * quantity
                total_cost += item_cost
                
                grocery_item = {
                    "name": kroger_result["name"],
                    "description": kroger_result.get("description", ""),
                    "quantity": quantity,
                    "unit": unit,
                    "price_per_unit": float(kroger_result["price"]),
                    "total_price": item_cost,
                    "image_url": kroger_result.get("image_url", ""),
                    "kroger_product_id": kroger_result.get("product_id", ""),
                    "category": kroger_result.get("category", "groceries"),
                    "brand": kroger_result.get("brand", ""),
                    "size": kroger_result.get("size", ""),
                    "available": True,
                    "source": "kroger"
                }
            else:
                # Not found on Kroger, use estimated price
                estimated_price = 2.50  # Default estimated price
                item_cost = estimated_price * quantity
                total_cost += item_cost
                
                grocery_item = {
                    "name": ingredient_name,
                    "description": f"Estimated price for {ingredient_name}",
                    "quantity": quantity,
                    "unit": unit,
                    "price_per_unit": estimated_price,
                    "total_price": item_cost,
                    "image_url": "",
                    "kroger_product_id": "",
                    "category": "groceries",
                    "brand": "Generic",
                    "size": "",
                    "available": False,
                    "source": "estimated"
                }
            
            grocery_items.append(grocery_item)
        
        # Create grocery list in database
        grocery_list = db_create_grocery_list(db, current_user.id, {
            "name": f"Grocery list for {recipe.title}",
            "store": "Kroger",
            "total_cost": total_cost,
            "items": grocery_items
        })
        
        # Generate Kroger order URL (if available)
        order_url = None
        if kroger_items_found > 0:
            # Create a basic Kroger search URL
            search_terms = "+".join([item["name"] for item in grocery_items[:3]])
            order_url = f"https://www.kroger.com/search?query={search_terms}"
        
        log_api_call("/grocery/from-recipe", "completed")
        logger.info(f"Created grocery list with {len(grocery_items)} items, {kroger_items_found} from Kroger")
        
        return {
            "list_id": grocery_list.id,
            "store": "Kroger",
            "items": grocery_items,
            "total_estimated_cost": total_cost,
            "kroger_items_found": kroger_items_found,
            "total_items": len(grocery_items),
            "order_url": order_url,
            "message": f"Found {kroger_items_found}/{len(grocery_items)} items on Kroger",
            "recipe_title": recipe.title
        }
        
    except Exception as e:
        logger.error(f"Grocery from recipe error: {e}")
        log_api_call("/grocery/from-recipe", "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating grocery list: {str(e)}"
        )


#==================== RECIPE MANAGEMENT ENDPOINTS ====================

@app.get("/recipes", tags=["Recipes"])
async def get_saved_recipes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's saved recipes"""
    recipes = db.query(Recipe).filter(Recipe.user_id == current_user.id).all()
    return {"recipes": recipes}


@app.post("/recipes/save", tags=["Recipes"])
async def save_recipe_endpoint(
    recipe_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a recipe to user's collection"""
    recipe = db_save_recipe(db, current_user.id, recipe_data)
    logger.info(f"Recipe saved by {current_user.username}: {recipe_data.get('title')}")
    return {"message": "Recipe saved successfully", "recipe": recipe}


@app.post("/recipes/{recipe_id}/favorite", tags=["Recipes"])
async def toggle_favorite(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle recipe favorite status"""
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    recipe.is_favorite = not recipe.is_favorite
    db.commit()
    
    return {"message": "Favorite status updated", "is_favorite": recipe.is_favorite}


# ==================== GROCERY LIST MANAGEMENT ====================

@app.get("/grocery-lists", tags=["Grocery"])
async def get_grocery_lists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's grocery lists"""
    lists = db.query(GroceryList).filter(GroceryList.user_id == current_user.id).all()
    return {"lists": lists}


@app.post("/grocery-lists/{list_id}/complete", tags=["Grocery"])
async def complete_grocery_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark grocery list as completed"""
    from datetime import datetime
    
    grocery_list = db.query(GroceryList).filter(
        GroceryList.id == list_id,
        GroceryList.user_id == current_user.id
    ).first()
    
    if not grocery_list:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    
    grocery_list.is_completed = True
    grocery_list.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Grocery list marked as completed"}


# ==================== MEAL LOGGING ====================

@app.post("/meals/log", tags=["Meals"])
async def log_meal_endpoint(
    meal_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a meal in history"""
    meal = db_log_meal(db, current_user.id, meal_data)
    logger.info(f"Meal logged by {current_user.username}: {meal_data.get('recipe_title')}")
    return {"message": "Meal logged successfully", "meal": meal}


@app.get("/meals/history", tags=["Meals"])
async def get_meal_history(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's meal history"""
    from datetime import datetime, timedelta
    
    since_date = datetime.utcnow() - timedelta(days=days)
    meals = db.query(MealHistory).filter(
        MealHistory.user_id == current_user.id,
        MealHistory.date >= since_date
    ).order_by(MealHistory.date.desc()).all()
    
    return {"meals": meals, "days": days}


# ==================== USER STATISTICS ====================

@app.get("/stats", tags=["User Stats"])
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    from sqlalchemy import func
    
    total_recipes = db.query(func.count(Recipe.id)).filter(
        Recipe.user_id == current_user.id
    ).scalar()
    
    total_grocery_lists = db.query(func.count(GroceryList.id)).filter(
        GroceryList.user_id == current_user.id
    ).scalar()
    
    total_meals = db.query(func.count(MealHistory.id)).filter(
        MealHistory.user_id == current_user.id
    ).scalar()
    
    favorite_recipes = db.query(func.count(Recipe.id)).filter(
        Recipe.user_id == current_user.id,
        Recipe.is_favorite == True
    ).scalar()
    
    return {
        "total_recipes": total_recipes,
        "favorite_recipes": favorite_recipes,
        "total_grocery_lists": total_grocery_lists,
        "total_meals_logged": total_meals
    }


# ==================== AGENT METADATA ====================

@app.get("/agents-metadata", tags=["System"])
async def get_agents_metadata():
    """
    Returns agent metadata for Agentverse registration.
    Metadata is embedded in each agent's docstring following ASI:One best practices.
    
    Reference: https://docs.agentverse.ai/documentation/getting-started/overview
    """
    return {
        "agents": [
            {
                "name": "RecipeAgent",
                "handle": "@agentic-grocery-recipes",
                "description": "Intelligent recipe generator using Claude AI that creates personalized meal options based on user preferences, dietary goals, and macros",
                "tags": ["nutrition", "recipes", "meal-planning", "fetchai", "agentic-ai", "claude", "ai-powered"],
                "endpoint": "http://localhost:8000/recipe",
                "version": "0.3.0",
                "protocol": "chat-protocol-v0.3.0",
                "capabilities": ["recipe_generation", "macro_calculation", "dietary_personalization", "claude_integration"]
            },
            {
                "name": "GroceryAgent",
                "handle": "@agentic-grocery-shopping",
                "description": "Automated grocery list builder that extracts ingredients from recipes and uses Kroger API for real product pricing and availability",
                "tags": ["grocery", "shopping", "kroger", "fetchai", "agentic-ai", "automation", "e-commerce"],
                "endpoint": "http://localhost:8000/grocery",
                "version": "0.3.0",
                "protocol": "chat-protocol-v0.3.0",
                "capabilities": ["ingredient_extraction", "price_estimation", "kroger_integration", "list_generation"]
            }
        ],
        "system": {
            "framework": "Fetch.ai uAgents",
            "api_framework": "FastAPI",
            "llm": "Anthropic Claude",
            "grocery_api": "Kroger",
            "database": "SQLite + SQLAlchemy",
            "authentication": "JWT",
            "documentation": "https://github.com/yourusername/agentic-grocery"
        }
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return {
        "error": "Not Found",
        "message": f"The endpoint {request.url.path} does not exist",
        "available_endpoints": {
            "public": ["/", "/health", "/agents-metadata", "/docs"],
            "auth": ["/auth/register", "/auth/login"],
            "user": ["/profile", "/stats"],
            "agents": ["/recipe", "/grocery"],
            "recipes": ["/recipes", "/recipes/save", "/recipes/{id}/favorite"],
            "grocery": ["/grocery-lists", "/grocery-lists/{id}/complete"],
            "meals": ["/meals/log", "/meals/history"]
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Starting Agentic Grocery API on {host}:{port}")
    logger.info("📚 API Documentation: http://localhost:8000/docs")
    logger.info("🔍 Alternative docs: http://localhost:8000/redoc")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

