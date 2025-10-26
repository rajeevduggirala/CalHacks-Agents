"""
Image Generation Service using Free Public APIs
Uses free text-to-image generation services
"""

import os
import urllib.parse
from typing import Optional

def initialize_image_model():
    """
    Placeholder for consistency with main.py initialization.
    No-op since we use external APIs.
    """
    print("✅ Image generation initialized (using public APIs)")
    pass


def generate_recipe_image(recipe_title: str, description: str, save_path: Optional[str] = None) -> str:
    """
    Generate a recipe image using free public text-to-image APIs.
    
    Uses multiple free services as fallbacks:
    1. Pollinations.ai (primary - fast and free)
    2. Placeholder (fallback)
    
    Args:
        recipe_title: Title of the recipe
        description: Description of the recipe
        save_path: Optional path to save the image file (not used with APIs)
    
    Returns:
        Image URL string
    """
    try:
        # Create descriptive prompt for better images
        prompt = f"professional food photography of {recipe_title}, {description}, high quality, appetizing, well plated, natural lighting, vibrant colors"
        
        # URL encode the prompt
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Use Pollinations.ai - free AI-generated images
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true&enhance=true"
        
        return image_url
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        # Fallback to placeholder
        return _generate_placeholder_url(recipe_title)


def _generate_placeholder_url(recipe_title: str) -> str:
    """Generate a placeholder URL if image generation fails"""
    safe_title = recipe_title.replace(' ', '+')
    return f"https://via.placeholder.com/512x512/FF6B6B/FFFFFF?text={safe_title}"


def is_model_loaded() -> bool:
    """Check if image generation is available"""
    return True
