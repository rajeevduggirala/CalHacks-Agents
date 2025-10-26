"""
Chroma VectorDB service for user preference learning
Stores and queries user preferences for recipe personalization
"""

import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Disable ChromaDB telemetry completely
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOFILE"] = "1"

# Suppress ChromaDB telemetry errors
import logging
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

class ChromaService:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            persist_directory="./chroma_db",
            anonymized_telemetry=False,
            allow_reset=True
        ))
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collections for different data types
        self.recipe_collection = self.client.get_or_create_collection(
            name="recipes",
            metadata={"description": "Recipe embeddings for similarity search"}
        )
        
        self.preference_collection = self.client.get_or_create_collection(
            name="user_preferences",
            metadata={"description": "User preference embeddings"}
        )
        
        self.user_context_collection = self.client.get_or_create_collection(
            name="user_context",
            metadata={"description": "User dietary context and history"}
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.embedding_model.encode(text).tolist()
    
    def store_recipe(self, recipe_data: Dict[str, Any], embedding: List[float]) -> str:
        """Store recipe in ChromaDB with embedding"""
        recipe_id = str(uuid.uuid4())
        
        self.recipe_collection.add(
            ids=[recipe_id],
            embeddings=[embedding],
            documents=[json.dumps(recipe_data)],
            metadatas=[{
                "user_id": recipe_data["user_id"],
                "meal_type": recipe_data["meal_type"],
                "cuisine": recipe_data.get("cuisine", ""),
                "calories": recipe_data.get("calories", 0),
                "created_at": datetime.utcnow().isoformat()
            }]
        )
        
        return recipe_id
    
    def store_user_preference(self, user_id: int, preference_data: Dict[str, Any], embedding: List[float]) -> str:
        """Store user preference in ChromaDB"""
        pref_id = str(uuid.uuid4())
        
        self.preference_collection.add(
            ids=[pref_id],
            embeddings=[embedding],
            documents=[json.dumps(preference_data)],
            metadatas=[{
                "user_id": user_id,
                "preference_type": preference_data["preference_type"],
                "item_type": preference_data["item_type"],
                "strength": preference_data.get("strength", 1.0),
                "created_at": datetime.utcnow().isoformat()
            }]
        )
        
        return pref_id
    
    def get_user_preferences(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's preference history"""
        results = self.preference_collection.get(
            where={"user_id": user_id},
            limit=limit
        )
        
        preferences = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                preferences.append({
                    "id": results["ids"][i],
                    "data": json.loads(doc),
                    "metadata": results["metadatas"][i]
                })
        
        return preferences
    
    def find_similar_recipes(self, user_id: int, query_embedding: List[float], 
                           meal_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find recipes similar to user preferences"""
        results = self.recipe_collection.query(
            query_embeddings=[query_embedding],
            where={"user_id": user_id, "meal_type": meal_type},
            n_results=limit
        )
        
        recipes = []
        for i, doc in enumerate(results["documents"][0]):
            recipes.append({
                "id": results["ids"][0][i],
                "data": json.loads(doc),
                "metadata": results["metadatas"][0][i],
                "similarity": results["distances"][0][i]
            })
        
        return recipes
    
    def get_user_dislikes(self, user_id: int) -> List[str]:
        """Get list of items user dislikes"""
        # Get all preferences for user, then filter for dislikes
        results = self.preference_collection.get(
            where={"user_id": user_id},
            limit=100
        )
        
        dislikes = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                data = json.loads(doc)
                if data.get("preference_type") == "disliked":
                    dislikes.append(data["item_name"])
        
        return dislikes
    
    def build_preference_context(self, preferences: List[Dict[str, Any]], dislikes: List[str]) -> str:
        """Build context string from user preferences"""
        context_parts = []
        
        # Add liked items
        liked_items = [p["data"]["item_name"] for p in preferences if p["data"]["preference_type"] == "liked"]
        if liked_items:
            context_parts.append(f"Likes: {', '.join(liked_items)}")
        
        # Add disliked items
        if dislikes:
            context_parts.append(f"Dislikes: {', '.join(dislikes)}")
        
        # Add context from preferences
        contexts = [p["data"].get("context", "") for p in preferences if p["data"].get("context")]
        if contexts:
            context_parts.append(f"Context: {'; '.join(contexts)}")
        
        return "; ".join(context_parts) if context_parts else "No specific preferences recorded"
