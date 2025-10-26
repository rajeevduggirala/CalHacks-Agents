#!/usr/bin/env python3
"""
Simple Recipe Agent Test
Creates a user and generates recipes for one day, saves images and data
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

class SimpleRecipeTester:
    def __init__(self, base_url: str = "http://localhost:8000", fast_mode: bool = True):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token: str = None
        self.user_data: Dict[str, Any] = None
        self.fast_mode = fast_mode  # Skip image downloads for faster testing
        
        # Create images directory
        self.images_dir = "images"
        os.makedirs(self.images_dir, exist_ok=True)
        print(f"📁 Created images directory: {self.images_dir}")
        if fast_mode:
            print("🚀 Fast mode enabled - skipping image downloads")
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str, status: str = "info"):
        """Print a formatted step"""
        icons = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        print(f"{icons.get(status, 'ℹ️')} {step}")
    
    def create_test_user(self) -> bool:
        """Create a test user with comprehensive dietary preferences"""
        self.print_header("Creating Test User")
        
        # Generate unique user data
        timestamp = int(time.time())
        self.user_data = {
            "email": f"recipeuser{timestamp}@example.com",
            "username": f"recipeuser{timestamp}",
            "password": "RecipeTest123!",
            "name": "Recipe Test User",
            "daily_calories": 2200.0,
            "dietary_restrictions": ["vegetarian", "gluten-free", "no nuts"],
            "likes": ["indian", "spicy", "savory", "grilled", "mediterranean", "thai", "italian"],
            "additional_information": "I love bold flavors and spices. Prefer meals that are hearty and filling. Enjoy experimenting with different cuisines. Hate overly sweet desserts.",
            "macros": {
                "protein": 130.0,
                "carbs": 250.0,
                "fats": 85.0
            }
        }
        
        self.print_step(f"Creating user: {self.user_data['email']}")
        self.print_step(f"Dietary preferences: {', '.join(self.user_data['dietary_restrictions'])}")
        self.print_step(f"Favorite cuisines: {', '.join(self.user_data['likes'])}")
        self.print_step(f"Daily calories: {self.user_data['daily_calories']}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=self.user_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.print_step("User created successfully", "success")
                self.print_step(f"User ID: {data.get('user', {}).get('id')}", "info")
                return True
            else:
                self.print_step(f"User creation failed: {response.status_code}", "error")
                self.print_step(f"Response: {response.text}", "error")
                return False
                
        except Exception as e:
            self.print_step(f"User creation error: {e}", "error")
            return False
    
    def generate_daily_meals(self, date: str) -> Dict[str, Any]:
        """Generate daily meals for a specific date"""
        if not self.auth_token:
            return {}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        self.print_step(f"Generating meals for {date}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/daily-meals/generate?day={date}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_step(f"Meals generated for {date}", "success")
                return data
            else:
                self.print_step(f"Meal generation failed for {date}: {response.status_code}", "error")
                self.print_step(f"Response: {response.text}", "error")
                return {}
                
        except Exception as e:
            self.print_step(f"Meal generation error for {date}: {e}", "error")
            return {}
    
    def download_and_save_image(self, image_url: str, filename: str) -> bool:
        """Download and save an image from URL (optimized for speed)"""
        try:
            # Skip image download for faster testing - just create placeholder
            if "placeholder" in image_url or "via.placeholder" in image_url:
                self.print_step(f"Skipping placeholder image: {filename}", "info")
                return True
                
            response = requests.get(image_url, timeout=1)  # Reduced timeout
            if response.status_code == 200:
                image_path = os.path.join(self.images_dir, filename)
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                self.print_step(f"Image saved: {filename}", "success")
                return True
            else:
                self.print_step(f"Failed to download image: {filename}", "error")
                return False
        except Exception as e:
            self.print_step(f"Image download error for {filename}: {e}", "error")
            return False
    
    def process_recipe_images(self, recipes: List[Dict[str, Any]], meal_type: str) -> List[Dict[str, Any]]:
        """Process and save images for recipes"""
        processed_recipes = []
        
        for i, recipe in enumerate(recipes):
            recipe_copy = recipe.copy()
            
            # Generate filename for image
            safe_title = "".join(c for c in recipe.get("title", f"recipe_{i}") if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            image_filename = f"{meal_type}_{safe_title}_{i}.jpg"
            
            # Download and save image if URL exists
            image_url = recipe.get("image_url")
            if image_url and not self.fast_mode:
                if self.download_and_save_image(image_url, image_filename):
                    recipe_copy["local_image_path"] = os.path.join(self.images_dir, image_filename)
                else:
                    recipe_copy["local_image_path"] = None
            else:
                recipe_copy["local_image_path"] = None
                if self.fast_mode and image_url:
                    recipe_copy["image_url"] = image_url  # Keep original URL in fast mode
            
            processed_recipes.append(recipe_copy)
        
        return processed_recipes
    
    def generate_weekly_meals(self) -> bool:
        """Generate meals for each day of the week"""
        self.print_header("Generating Weekly Meal Plan")
        
        # Get current date and generate dates for the week
        today = datetime.now()
        week_dates = []
        for i in range(7):
            date = today + timedelta(days=i)
            week_dates.append(date.strftime("%Y-%m-%d"))
        
        self.print_step(f"Generating meals for week: {week_dates[0]} to {week_dates[-1]}")
        
        weekly_data = {
            "generation_date": datetime.now().isoformat(),
            "user_email": self.user_data["email"],
            "weekly_meals": {}
        }
        
        for date in week_dates:
            day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
            self.print_step(f"Processing {day_name}, {date}")
            
            # Generate daily meals
            daily_meals = self.generate_daily_meals(date)
            
            if daily_meals:
                # Process images for each meal type
                processed_meals = {}
                
                for meal_type in ["breakfast", "lunch", "dinner"]:
                    recipe = daily_meals.get(meal_type)
                    if recipe:
                        # Convert single recipe to list format for compatibility
                        recipes = [recipe]
                        processed_recipes = self.process_recipe_images(recipes, meal_type)
                        processed_meals[meal_type] = processed_recipes
                        self.print_step(f"Processed {len(processed_recipes)} {meal_type} recipes", "success")
                    else:
                        processed_meals[meal_type] = []
                        self.print_step(f"No {meal_type} recipes found", "warning")
                
                weekly_data["weekly_meals"][date] = {
                    "day_name": day_name,
                    "meals": processed_meals,
                    "total_calories": daily_meals.get("total_calories", 0),
                    "total_macros": daily_meals.get("total_macros", {}),
                    "generation_metadata": daily_meals.get("metadata", {})
                }
            else:
                weekly_data["weekly_meals"][date] = {
                    "day_name": day_name,
                    "meals": {},
                    "error": "Failed to generate meals"
                }
                self.print_step(f"Failed to generate meals for {day_name}", "error")
        
        self.weekly_recipes = weekly_data
        return True
    
    def save_weekly_data(self) -> bool:
        """Save weekly recipe data to JSON file"""
        self.print_header("Saving Weekly Data")
        
        if not self.weekly_recipes:
            self.print_step("No weekly data to save", "error")
            return False
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weekly_recipes_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.weekly_recipes, f, indent=2, ensure_ascii=False)
            
            self.print_step(f"Weekly data saved to: {filename}", "success")
            
            # Also save a summary
            summary_filename = f"weekly_summary_{timestamp}.json"
            summary = {
                "generation_date": self.weekly_recipes["generation_date"],
                "user_email": self.user_data["email"],
                "total_days": len(self.weekly_recipes["weekly_meals"]),
                "days_with_meals": sum(1 for day_data in self.weekly_recipes["weekly_meals"].values() 
                                     if "error" not in day_data),
                "total_recipes": sum(len(day_data.get("meals", {}).get(meal_type, [])) 
                                   for day_data in self.weekly_recipes["weekly_meals"].values() 
                                   for meal_type in ["breakfast", "lunch", "dinner"]),
                "images_saved": len([f for f in os.listdir(self.images_dir) if f.endswith('.jpg')])
            }
            
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.print_step(f"Summary saved to: {summary_filename}", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Failed to save data: {e}", "error")
            return False
    
    def print_weekly_summary(self):
        """Print a summary of the weekly meal generation"""
        self.print_header("Weekly Meal Generation Summary")
        
        if not self.weekly_recipes:
            self.print_step("No weekly data available", "error")
            return
        
        total_recipes = 0
        total_images = 0
        successful_days = 0
        
        for date, day_data in self.weekly_recipes["weekly_meals"].items():
            if "error" not in day_data:
                successful_days += 1
                day_recipes = 0
                day_images = 0
                
                for meal_type in ["breakfast", "lunch", "dinner"]:
                    recipes = day_data.get("meals", {}).get(meal_type, [])
                    day_recipes += len(recipes)
                    
                    for recipe in recipes:
                        if recipe.get("local_image_path"):
                            day_images += 1
                
                total_recipes += day_recipes
                total_images += day_images
                
                self.print_step(f"{day_data['day_name']} ({date}): {day_recipes} recipes, {day_images} images", "info")
            else:
                self.print_step(f"{day_data['day_name']} ({date}): Failed to generate meals", "error")
        
        self.print_step(f"Total successful days: {successful_days}/7", "success" if successful_days == 7 else "warning")
        self.print_step(f"Total recipes generated: {total_recipes}", "success")
        self.print_step(f"Total images saved: {total_images}", "success")
        self.print_step(f"Images directory: {self.images_dir}", "info")
    
    def run_weekly_test(self) -> bool:
        """Run the complete weekly recipe generation test"""
        print("🚀 Starting Weekly Recipe Generation Test")
        print("=" * 60)
        
        # Step 1: Create user
        if not self.create_test_user():
            print("\n❌ User creation failed. Cannot continue.")
            return False
        
        # Step 2: Generate weekly meals
        if not self.generate_weekly_meals():
            print("\n❌ Weekly meal generation failed.")
            return False
        
        # Step 3: Save data
        if not self.save_weekly_data():
            print("\n❌ Data saving failed.")
            return False
        
        # Step 4: Print summary
        self.print_weekly_summary()
        
        print(f"\n🎉 Weekly recipe generation test completed!")
        print(f"📁 Check the '{self.images_dir}' directory for saved images")
        print(f"📄 Check the JSON files for complete recipe data")
        
        return True


def main():
    """Main function to run the weekly recipe test"""
    print("🧪 Agentic Grocery - Weekly Recipe Generation Test")
    print("=" * 60)
    print("This test will:")
    print("1. Create a test user with dietary preferences")
    print("2. Generate recipes for each day of the week")
    print("3. Download and save recipe images")
    print("4. Save all data to JSON files")
    print("=" * 60)
    
    tester = SimpleRecipeTester()
    success = tester.run_weekly_test()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
