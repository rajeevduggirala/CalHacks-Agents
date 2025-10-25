"""
ChatAgent - Conversational Coordinator for Agentic Grocery
Handles user input, extracts intent, dietary context, and preferences.
Forwards structured requests to RecipeAgent.
ASI:One compatible with Chat Protocol v0.3.0

Agent Metadata:
- Name: ChatAgent
- Description: Conversational entrypoint for Agentic Grocery - handles user queries, 
               extracts dietary preferences, and coordinates with other agents
- Tags: nutrition, recipes, fetchai, agentic-ai, chatbot, conversation
- Endpoint: http://localhost:8000/chat
- Version: 0.3.0
- Protocol: chat-protocol-v0.3.0
"""

import os
import json
from typing import Dict, Any, Optional
from uagents import Agent, Context, Model
from pydantic import BaseModel, Field
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.logger import setup_logger, log_agent_message


# Pydantic models for structured communication
class ChatRequest(BaseModel):
    """User chat request model"""
    user_id: str = Field(default="raj", description="User identifier")
    message: str = Field(..., description="User's message/query")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


class ChatResponse(BaseModel):
    """Chat response model"""
    agent: str = Field(default="ChatAgent", description="Agent name")
    message: str = Field(..., description="Response message")
    structured_data: Optional[Dict[str, Any]] = Field(default=None, description="Structured data for next agent")
    next_action: Optional[str] = Field(default=None, description="Next action to take")


class RecipeRequest(BaseModel):
    """Structured recipe request for RecipeAgent"""
    user_profile: Dict[str, Any]
    preferences: Dict[str, Any]
    context: Dict[str, Any]


# Initialize ChatAgent
CHAT_AGENT_SEED = os.getenv("CHAT_AGENT_SEED", "chat-agent-seed-12345")
chat_agent = Agent(
    name="ChatAgent",
    seed=CHAT_AGENT_SEED,
    port=8001,
    endpoint=["http://localhost:8001/submit"]
)

logger = setup_logger("ChatAgent")


def load_user_profile(user_id: str = "raj") -> Dict[str, Any]:
    """Load user profile from data directory"""
    try:
        profile_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "user_profile.json"
        )
        with open(profile_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load user profile: {e}")
        return {}


def extract_preferences(message: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract dietary preferences and intent from user message.
    In production, this would use NLP/LLM to parse the message.
    For now, uses simple keyword matching.
    """
    message_lower = message.lower()
    
    preferences = {
        "meal_type": None,
        "cook_time": None,
        "cuisine": None,
        "dietary_restrictions": user_profile.get("diet", ""),
        "likes": user_profile.get("likes", []),
        "dislikes": user_profile.get("dislikes", [])
    }
    
    # Extract meal type
    if any(word in message_lower for word in ["breakfast", "morning"]):
        preferences["meal_type"] = "breakfast"
    elif any(word in message_lower for word in ["lunch", "noon"]):
        preferences["meal_type"] = "lunch"
    elif any(word in message_lower for word in ["dinner", "evening"]):
        preferences["meal_type"] = "dinner"
    elif any(word in message_lower for word in ["snack"]):
        preferences["meal_type"] = "snack"
    
    # Extract cook time
    if any(word in message_lower for word in ["quick", "fast", "15", "20"]):
        preferences["cook_time"] = "15-30 mins"
    elif any(word in message_lower for word in ["30", "45"]):
        preferences["cook_time"] = "30-45 mins"
    elif "hour" in message_lower or "60" in message_lower:
        preferences["cook_time"] = "45-60 mins"
    
    # Extract cuisine
    cuisines = ["indian", "italian", "chinese", "mexican", "thai", "japanese"]
    for cuisine in cuisines:
        if cuisine in message_lower:
            preferences["cuisine"] = cuisine
            break
    
    return preferences


def is_request_complete(preferences: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Check if we have enough information to proceed with recipe generation.
    Returns (is_complete, missing_info_message)
    """
    if not preferences.get("meal_type"):
        return False, "What meal are you planning? (breakfast, lunch, dinner, or snack)"
    
    if not preferences.get("cook_time"):
        return False, "How much time do you have to cook? (e.g., 15-30 mins, 30-45 mins)"
    
    return True, None


@chat_agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup handler"""
    log_agent_message("ChatAgent", "🚀 ChatAgent started and ready!")
    logger.info(f"Agent address: {ctx.agent.address}")


@chat_agent.on_message(model=ChatRequest)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatRequest):
    """
    Main message handler for ChatAgent.
    Compatible with ASI:One Chat Protocol v0.3.0
    """
    log_agent_message("ChatAgent", f"📨 Received message: {msg.message}")
    
    # Load user profile
    user_profile = load_user_profile(msg.user_id)
    
    # Extract preferences from message
    preferences = extract_preferences(msg.message, user_profile)
    
    # Check if we have enough information
    is_complete, missing_info = is_request_complete(preferences)
    
    if not is_complete:
        # Need more information from user
        response = ChatResponse(
            message=missing_info,
            next_action="await_user_input"
        )
        log_agent_message("ChatAgent", f"⏳ Requesting more info: {missing_info}")
    else:
        # Ready to generate recipes
        recipe_request = RecipeRequest(
            user_profile=user_profile,
            preferences=preferences,
            context={
                "original_message": msg.message,
                "session_id": msg.session_id
            }
        )
        
        response = ChatResponse(
            message="Great! Let me find some recipes for you...",
            structured_data=recipe_request.model_dump(),
            next_action="generate_recipes"
        )
        log_agent_message("ChatAgent", "✅ Request complete, forwarding to RecipeAgent")
    
    # Send response back
    await ctx.send(sender, response)


@chat_agent.on_interval(period=60.0)
async def periodic_health_check(ctx: Context):
    """Periodic health check - logs agent status"""
    logger.debug(f"ChatAgent health check - Address: {ctx.agent.address}")


def process_chat(user_message: str, user_id: str = "raj") -> Dict[str, Any]:
    """
    Synchronous wrapper for processing chat messages.
    Used by FastAPI endpoints.
    """
    user_profile = load_user_profile(user_id)
    preferences = extract_preferences(user_message, user_profile)
    is_complete, missing_info = is_request_complete(preferences)
    
    if not is_complete:
        return {
            "agent": "ChatAgent",
            "message": missing_info,
            "next_action": "await_user_input",
            "structured_data": None
        }
    else:
        recipe_request = {
            "user_profile": user_profile,
            "preferences": preferences,
            "context": {
                "original_message": user_message
            }
        }
        
        return {
            "agent": "ChatAgent",
            "message": "Great! Let me find some recipes for you...",
            "next_action": "generate_recipes",
            "structured_data": recipe_request
        }


if __name__ == "__main__":
    log_agent_message("ChatAgent", "Starting ChatAgent...")
    chat_agent.run()

