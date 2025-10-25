"""
Agentic Grocery - FastAPI Backend
Multi-agent system for food recommendation and grocery automation
Integrates Fetch.ai's uAgents with FastAPI for ASI:One compatibility
Includes authentication, user management, and SQLite database
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Import agent modules
from agents.chat_agent.agent import process_chat
from agents.recipe_agent.agent import generate_recipes
from agents.grocery_agent.agent import generate_grocery_list
from utils.logger import setup_logger, log_api_call

# Import database and auth
from database import (
    get_db, init_db, create_user, get_user_by_email, get_user_by_username,
    create_user_profile, save_recipe as db_save_recipe,
    create_grocery_list as db_create_grocery_list, log_meal as db_log_meal,
    User, UserProfile, SavedRecipe, GroceryList, MealHistory
)
from auth import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("AgenticGrocery")

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
class ChatRequest(BaseModel):
    """Chat endpoint request model"""
    message: str = Field(..., description="User's message/query", min_length=1)
    user_id: str = Field(default="raj", description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


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
class UserRegister(BaseModel):
    """User registration model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    user: Dict[str, Any]


class UserProfileUpdate(BaseModel):
    """User profile update model"""
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    goal: Optional[str] = None
    workout_frequency: Optional[str] = None
    activity_level: Optional[str] = None
    diet: Optional[str] = None
    allergies: Optional[List[str]] = None
    likes: Optional[List[str]] = None
    dislikes: Optional[List[str]] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    target_calories: Optional[float] = None


# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Agentic Grocery API",
        "version": "0.3.0",
        "description": "Multi-agent system for food recommendations and grocery automation",
        "features": ["Multi-Agent AI", "Claude Recipes", "Kroger Integration", "User Authentication"],
        "agents": ["ChatAgent", "RecipeAgent", "GroceryAgent"],
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
    Register a new user account
    
    Creates a new user with email, username, and hashed password.
    Returns JWT token for immediate authentication.
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
    
    # Create user
    user = create_user(db, user_data.email, user_data.username, user_data.password)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    log_api_call("/auth/register", "completed")
    logger.info(f"New user registered: {user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
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
            "username": user.username
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
    
    Requires authentication. Returns user info and dietary profile.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "created_at": current_user.created_at
        },
        "profile": profile
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
                "ChatAgent": "operational",
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


@app.post("/chat", tags=["Agents"])
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat endpoint - sends user message to ChatAgent
    
    **Requires Authentication**
    
    ChatAgent extracts intent, dietary preferences, and coordinates with other agents.
    Uses authenticated user's profile for personalized responses.
    
    Args:
        request: ChatRequest with user message
        current_user: Authenticated user (from JWT token)
    
    Returns:
        Response from ChatAgent with next action
    """
    log_api_call("/chat", "started")
    logger.info(f"Processing chat message for user {current_user.username}: {request.message}")
    
    try:
        # Process chat through ChatAgent using actual username
        response = process_chat(request.message, current_user.username)
        
        log_api_call("/chat", "completed")
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        log_api_call("/chat", "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
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


@app.post("/full-flow", tags=["Workflows"])
async def full_flow_endpoint(request: ChatRequest):
    """
    Full workflow endpoint - demonstrates complete flow from chat to grocery list
    
    This endpoint:
    1. Processes user message through ChatAgent
    2. Generates recipes through RecipeAgent
    3. Creates grocery list for first recipe through GroceryAgent
    
    Args:
        request: ChatRequest with user message
    
    Returns:
        Complete workflow result with recipes and grocery list
    """
    log_api_call("/full-flow", "started")
    logger.info(f"Starting full flow for: {request.message}")
    
    try:
        # Step 1: Chat
        chat_response = process_chat(request.message, request.user_id)
        
        if chat_response.get("next_action") != "generate_recipes":
            # Need more information from user
            return {
                "step": "chat",
                "chat_response": chat_response,
                "message": "Need more information to proceed"
            }
        
        # Step 2: Generate Recipes
        recipe_request = chat_response.get("structured_data")
        recipe_response = generate_recipes(recipe_request)
        
        recipes = recipe_response.get("recipes", [])
        if not recipes:
            return {
                "step": "recipe",
                "error": "No recipes generated",
                "chat_response": chat_response,
                "recipe_response": recipe_response
            }
        
        # Step 3: Generate Grocery List for first recipe
        first_recipe = recipes[0]
        grocery_request = {
            "recipe": first_recipe,
            "user_id": request.user_id,
            "store_preference": "Kroger"
        }
        grocery_response = generate_grocery_list(grocery_request)
        
        log_api_call("/full-flow", "completed")
        
        return {
            "step": "complete",
            "chat_response": chat_response,
            "recipe_response": recipe_response,
            "grocery_response": grocery_response,
            "message": "Full workflow completed successfully!"
        }
        
    except Exception as e:
        logger.error(f"Full flow error: {e}")
        log_api_call("/full-flow", "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in full flow: {str(e)}"
        )


#==================== RECIPE MANAGEMENT ENDPOINTS ====================

@app.get("/recipes", tags=["Recipes"])
async def get_saved_recipes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's saved recipes"""
    recipes = db.query(SavedRecipe).filter(SavedRecipe.user_id == current_user.id).all()
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
    recipe = db.query(SavedRecipe).filter(
        SavedRecipe.id == recipe_id,
        SavedRecipe.user_id == current_user.id
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
    
    total_recipes = db.query(func.count(SavedRecipe.id)).filter(
        SavedRecipe.user_id == current_user.id
    ).scalar()
    
    total_grocery_lists = db.query(func.count(GroceryList.id)).filter(
        GroceryList.user_id == current_user.id
    ).scalar()
    
    total_meals = db.query(func.count(MealHistory.id)).filter(
        MealHistory.user_id == current_user.id
    ).scalar()
    
    favorite_recipes = db.query(func.count(SavedRecipe.id)).filter(
        SavedRecipe.user_id == current_user.id,
        SavedRecipe.is_favorite == True
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
                "name": "ChatAgent",
                "handle": "@agentic-grocery-chat",
                "description": "Conversational entrypoint for Agentic Grocery - handles user queries, extracts dietary preferences, and coordinates with other agents",
                "tags": ["nutrition", "recipes", "fetchai", "agentic-ai", "chatbot", "conversation"],
                "endpoint": "http://localhost:8000/chat",
                "version": "0.3.0",
                "protocol": "chat-protocol-v0.3.0",
                "capabilities": ["preference_extraction", "intent_classification", "workflow_coordination"]
            },
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
            "agents": ["/chat", "/recipe", "/grocery"],
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

