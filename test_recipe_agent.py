#!/usr/bin/env python3
"""
Comprehensive test script for Recipe Agent endpoints
Tests all recipe-related functionality including authentication
"""

import requests
import json
import sys
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

console = Console()
BASE_URL = "http://localhost:8000"

def print_response(title: str, response: requests.Response):
    """Pretty print API response"""
    console.print(f"\n[bold cyan]═══ {title} ═══[/bold cyan]")
    console.print(f"[yellow]Status Code:[/yellow] {response.status_code}")
    
    if response.status_code in [200, 201]:
        console.print(Panel(JSON(response.text), title="Response", border_style="green"))
    else:
        console.print(Panel(response.text, title="Error", border_style="red"))

def register_test_user():
    """Register a test user and return auth token"""
    console.print("\n[bold green]🔐 Registering test user...[/bold green]")
    
    user_data = {
        "email": "test@recipeagent.com",
        "username": "recipe_tester",
        "password": "testpassword123",
        "name": "Recipe Tester",
        "daily_calories": 2000.0,
        "dietary_restrictions": ["vegetarian", "no nuts"],
        "likes": ["indian", "spicy", "savory"],
        "additional_information": "I love garlic and prefer quick meals"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print_response("User Registration", response)
    
    if response.status_code == 201:
        return response.json()["access_token"]
    else:
        console.print("[bold red]❌ Failed to register test user[/bold red]")
        return None

def test_recipe_endpoint(token: str):
    """Test the main recipe endpoint"""
    console.print("\n[bold green]🍳 Testing Recipe Endpoint...[/bold green]")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    recipe_request = {
        "user_profile": {
            "height_cm": 175,
            "weight_kg": 70,
            "goal": "cut",
            "diet": "vegetarian",
            "workout_frequency": "5/week",
            "likes": ["spicy", "indian"],
            "dislikes": ["mushrooms"],
            "allergies": [],
            "target_macros": {
                "protein_g": 140,
                "carbs_g": 200,
                "fat_g": 50,
                "calories": 1800
            }
        },
        "preferences": {
            "meal_type": "dinner",
            "cook_time": "30-45 mins",
            "cuisine": "indian",
            "dietary_restrictions": "vegetarian"
        },
        "context": {
            "occasion": "weekday dinner",
            "mood": "comfort food"
        }
    }
    
    console.print("[yellow]Request:[/yellow]")
    console.print(JSON(json.dumps(recipe_request)))
    
    response = requests.post(f"{BASE_URL}/recipe", json=recipe_request, headers=headers)
    print_response("Recipe Generation", response)
    
    if response.status_code == 200:
        recipe_data = response.json()
        recipes = recipe_data.get('recipes', [])
        console.print(f"[green]✅ Generated {len(recipes)} recipes successfully![/green]")
        
        if recipes:
            first_recipe = recipes[0]
            console.print(f"[green]📋 First recipe: {first_recipe.get('title', 'Unknown')}[/green]")
            console.print(f"[green]🍽️  Servings: {first_recipe.get('servings', 'Unknown')}[/green]")
            console.print(f"[green]⏱️  Cook time: {first_recipe.get('cook_time', 'Unknown')}[/green]")
            
            # Check if macros are present
            macros = first_recipe.get('macros', {})
            if macros:
                console.print(f"[green]📊 Macros - Protein: {macros.get('protein', 'N/A')}g, Carbs: {macros.get('carbs', 'N/A')}g, Fat: {macros.get('fat', 'N/A')}g[/green]")
        
        return recipe_data
    else:
        console.print("[bold red]❌ Recipe endpoint failed[/bold red]")
        return None

def test_daily_meals_endpoint(token: str):
    """Test the daily meals endpoint"""
    console.print("\n[bold green]📅 Testing Daily Meals Endpoint...[/bold green]")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test generating meals for Monday
    response = requests.post(f"{BASE_URL}/daily-meals/generate-by-day?day=Monday", headers=headers)
    print_response("Daily Meals Generation", response)
    
    if response.status_code == 200:
        meals_data = response.json()
        console.print("[green]✅ Daily meals generated successfully![/green]")
        
        # Check each meal type
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if meal_type in meals_data:
                meal = meals_data[meal_type]
                console.print(f"[green]🍽️  {meal_type.title()}: {meal.get('title', 'Unknown')}[/green]")
                console.print(f"[green]   Calories: {meal.get('calories', 'N/A')}, Protein: {meal.get('protein', 'N/A')}g[/green]")
        
        return meals_data
    else:
        console.print("[bold red]❌ Daily meals endpoint failed[/bold red]")
        return None

def test_grocery_endpoint(token: str, recipe_data: dict):
    """Test the grocery endpoint with a generated recipe"""
    console.print("\n[bold green]🛒 Testing Grocery Endpoint...[/bold green]")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if not recipe_data or not recipe_data.get('recipes'):
        console.print("[yellow]⚠️  No recipe data available for grocery test[/yellow]")
        return None
    
    # Use the first recipe from the recipe endpoint
    first_recipe = recipe_data['recipes'][0]
    
    grocery_request = {
        "recipe": {
            "title": first_recipe.get('title', 'Test Recipe'),
            "ingredients": first_recipe.get('ingredients', []),
            "servings": first_recipe.get('servings', 1),
            "description": first_recipe.get('description', '')
        },
        "user_id": "recipe_tester",
        "store_preference": "Kroger"
    }
    
    console.print("[yellow]Request:[/yellow]")
    console.print(JSON(json.dumps(grocery_request)))
    
    response = requests.post(f"{BASE_URL}/grocery", json=grocery_request, headers=headers)
    print_response("Grocery List Generation", response)
    
    if response.status_code == 200:
        grocery_data = response.json()
        items = grocery_data.get('items', [])
        total_cost = grocery_data.get('total_estimated_cost', 0)
        console.print(f"[green]✅ Grocery list created with {len(items)} items[/green]")
        console.print(f"[green]💰 Total estimated cost: ${total_cost:.2f}[/green]")
        return grocery_data
    else:
        console.print("[bold red]❌ Grocery endpoint failed[/bold red]")
        return None

def test_recipe_save_endpoint(token: str, recipe_data: dict):
    """Test saving a recipe"""
    console.print("\n[bold green]💾 Testing Recipe Save Endpoint...[/bold green]")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if not recipe_data or not recipe_data.get('recipes'):
        console.print("[yellow]⚠️  No recipe data available for save test[/yellow]")
        return None
    
    # Use the first recipe
    first_recipe = recipe_data['recipes'][0]
    
    response = requests.post(f"{BASE_URL}/recipes/save", json=first_recipe, headers=headers)
    print_response("Recipe Save", response)
    
    if response.status_code == 200:
        console.print("[green]✅ Recipe saved successfully![/green]")
        return response.json()
    else:
        console.print("[bold red]❌ Recipe save failed[/bold red]")
        return None

def test_recipe_retrieval_endpoint(token: str):
    """Test retrieving saved recipes"""
    console.print("\n[bold green]📚 Testing Recipe Retrieval Endpoint...[/bold green]")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/recipes", headers=headers)
    print_response("Recipe Retrieval", response)
    
    if response.status_code == 200:
        recipes_data = response.json()
        recipes = recipes_data.get('recipes', [])
        console.print(f"[green]✅ Retrieved {len(recipes)} saved recipes[/green]")
        return recipes_data
    else:
        console.print("[bold red]❌ Recipe retrieval failed[/bold red]")
        return None

def main():
    """Run comprehensive recipe agent tests"""
    console.print(Panel.fit(
        "[bold yellow]🧪 Recipe Agent Comprehensive Test Suite[/bold yellow]\n"
        f"Testing server at: {BASE_URL}",
        border_style="cyan"
    ))
    
    try:
        # Step 1: Register test user and get token
        token = register_test_user()
        if not token:
            console.print("[bold red]❌ Cannot proceed without authentication token[/bold red]")
            return
        
        # Step 2: Test recipe generation
        recipe_data = test_recipe_endpoint(token)
        
        # Step 3: Test daily meals generation
        meals_data = test_daily_meals_endpoint(token)
        
        # Step 4: Test grocery list generation (if we have recipe data)
        grocery_data = test_grocery_endpoint(token, recipe_data)
        
        # Step 5: Test recipe saving (if we have recipe data)
        save_data = test_recipe_save_endpoint(token, recipe_data)
        
        # Step 6: Test recipe retrieval
        retrieval_data = test_recipe_retrieval_endpoint(token)
        
        # Summary
        console.print("\n[bold green]═══════════════════════════════[/bold green]")
        console.print("[bold green]🎉 Recipe Agent Test Summary[/bold green]")
        console.print("[bold green]═══════════════════════════════[/bold green]")
        
        tests_passed = 0
        total_tests = 5
        
        if recipe_data:
            tests_passed += 1
            console.print("[green]✅ Recipe Generation: PASSED[/green]")
        else:
            console.print("[red]❌ Recipe Generation: FAILED[/red]")
        
        if meals_data:
            tests_passed += 1
            console.print("[green]✅ Daily Meals Generation: PASSED[/green]")
        else:
            console.print("[red]❌ Daily Meals Generation: FAILED[/red]")
        
        if grocery_data:
            tests_passed += 1
            console.print("[green]✅ Grocery List Generation: PASSED[/green]")
        else:
            console.print("[red]❌ Grocery List Generation: FAILED[/red]")
        
        if save_data:
            tests_passed += 1
            console.print("[green]✅ Recipe Saving: PASSED[/green]")
        else:
            console.print("[red]❌ Recipe Saving: FAILED[/red]")
        
        if retrieval_data:
            tests_passed += 1
            console.print("[green]✅ Recipe Retrieval: PASSED[/green]")
        else:
            console.print("[red]❌ Recipe Retrieval: FAILED[/red]")
        
        console.print(f"\n[bold cyan]📊 Results: {tests_passed}/{total_tests} tests passed[/bold cyan]")
        
        if tests_passed == total_tests:
            console.print("\n[bold green]🎉 All Recipe Agent tests passed! The system is fully functional.[/bold green]")
        else:
            console.print(f"\n[bold yellow]⚠️  {total_tests - tests_passed} tests failed. Please check the errors above.[/bold yellow]")
        
    except requests.exceptions.ConnectionError:
        console.print("\n[bold red]❌ Connection Error![/bold red]")
        console.print("[yellow]Is the server running? Start it with: python main.py[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected Error: {e}[/bold red]")

if __name__ == "__main__":
    main()
