#!/usr/bin/env python3
"""
Test script for Agentic Grocery API
Demonstrates all endpoints with example requests
"""

import requests
import json
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

console = Console()
BASE_URL = "http://localhost:8000"


def print_response(title: str, response: requests.Response):
    """Pretty print API response"""
    console.print(f"\n[bold cyan]═══ {title} ═══[/bold cyan]")
    console.print(f"[yellow]Status Code:[/yellow] {response.status_code}")
    
    if response.status_code == 200:
        console.print(Panel(JSON(response.text), title="Response", border_style="green"))
    else:
        console.print(Panel(response.text, title="Error", border_style="red"))


def test_health():
    """Test health endpoint"""
    console.print("\n[bold green]Testing Health Endpoint...[/bold green]")
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    return response.status_code == 200


def test_chat():
    """Test chat endpoint"""
    console.print("\n[bold green]Testing Chat Endpoint...[/bold green]")
    
    data = {
        "message": "I want a high protein vegetarian dinner, quick to make",
        "user_id": "raj"
    }
    
    console.print("[yellow]Request:[/yellow]")
    console.print(JSON(json.dumps(data)))
    
    response = requests.post(f"{BASE_URL}/chat", json=data)
    print_response("Chat Response", response)
    return response.json() if response.status_code == 200 else None


def test_recipe():
    """Test recipe endpoint"""
    console.print("\n[bold green]Testing Recipe Endpoint...[/bold green]")
    
    data = {
        "user_profile": {
            "height_cm": 175,
            "weight_kg": 70,
            "goal": "cut",
            "diet": "vegetarian",
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
        }
    }
    
    console.print("[yellow]Request:[/yellow]")
    console.print(JSON(json.dumps(data)))
    
    response = requests.post(f"{BASE_URL}/recipe", json=data)
    print_response("Recipe Response", response)
    return response.json() if response.status_code == 200 else None


def test_grocery(recipe=None):
    """Test grocery endpoint"""
    console.print("\n[bold green]Testing Grocery Endpoint...[/bold green]")
    
    # Use provided recipe or default
    if recipe is None:
        recipe = {
            "title": "Paneer Tikka with Quinoa",
            "ingredients": [
                {"name": "paneer (cottage cheese)", "quantity": "200g"},
                {"name": "quinoa", "quantity": "1/2 cup"},
                {"name": "yogurt", "quantity": "1/4 cup"},
                {"name": "garam masala", "quantity": "1 tsp"},
                {"name": "bell peppers", "quantity": "1 cup"}
            ]
        }
    
    data = {
        "recipe": recipe,
        "user_id": "raj",
        "store_preference": "Kroger"
    }
    
    console.print("[yellow]Request:[/yellow]")
    console.print(JSON(json.dumps(data)))
    
    response = requests.post(f"{BASE_URL}/grocery", json=data)
    print_response("Grocery Response", response)
    return response.json() if response.status_code == 200 else None


def test_full_flow():
    """Test full workflow endpoint"""
    console.print("\n[bold green]Testing Full Flow Endpoint...[/bold green]")
    
    data = {
        "message": "I need a high protein vegetarian lunch that takes 30 minutes",
        "user_id": "raj"
    }
    
    console.print("[yellow]Request:[/yellow]")
    console.print(JSON(json.dumps(data)))
    
    response = requests.post(f"{BASE_URL}/full-flow", json=data)
    print_response("Full Flow Response", response)
    return response.json() if response.status_code == 200 else None


def test_agents_metadata():
    """Test agents metadata endpoint"""
    console.print("\n[bold green]Testing Agents Metadata Endpoint...[/bold green]")
    response = requests.get(f"{BASE_URL}/agents-metadata")
    print_response("Agents Metadata", response)
    return response.json() if response.status_code == 200 else None


def main():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold yellow]Agentic Grocery API Test Suite[/bold yellow]\n"
        f"Testing server at: {BASE_URL}",
        border_style="cyan"
    ))
    
    try:
        # Test 1: Health Check
        if not test_health():
            console.print("[bold red]❌ Server is not running![/bold red]")
            console.print(f"[yellow]Please start the server with: python main.py[/yellow]")
            return
        
        # Test 2: Chat
        chat_result = test_chat()
        
        # Test 3: Recipe
        recipe_result = test_recipe()
        
        # Test 4: Grocery (use first recipe if available)
        if recipe_result and recipe_result.get('recipes'):
            first_recipe = recipe_result['recipes'][0]
            grocery_result = test_grocery(first_recipe)
        else:
            grocery_result = test_grocery()
        
        # Test 5: Full Flow
        full_flow_result = test_full_flow()
        
        # Test 6: Agents Metadata
        metadata_result = test_agents_metadata()
        
        # Summary
        console.print("\n[bold green]═══════════════════════════════[/bold green]")
        console.print("[bold green]✅ All tests completed![/bold green]")
        console.print("[bold green]═══════════════════════════════[/bold green]")
        
        if full_flow_result and full_flow_result.get('step') == 'complete':
            console.print("\n[bold cyan]🎉 Full workflow successful![/bold cyan]")
            recipes = full_flow_result.get('recipe_response', {}).get('recipes', [])
            console.print(f"[green]Generated {len(recipes)} recipes[/green]")
            
            grocery = full_flow_result.get('grocery_response', {})
            items = grocery.get('items', [])
            total_cost = grocery.get('total_estimated_cost', 0)
            console.print(f"[green]Created grocery list with {len(items)} items[/green]")
            console.print(f"[green]Total estimated cost: ${total_cost}[/green]")
        
    except requests.exceptions.ConnectionError:
        console.print("\n[bold red]❌ Connection Error![/bold red]")
        console.print("[yellow]Is the server running? Start it with: python main.py[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")


if __name__ == "__main__":
    main()

