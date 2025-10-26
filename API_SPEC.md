# Agentic Grocery API Specification

**Version:** 0.3.0  
**Base URL:** `http://localhost:8000` (or your deployed URL)  
**Authentication:** Bearer Token (JWT)

## Overview

The Agentic Grocery API is a multi-agent system that generates personalized recipes and creates grocery lists integrated with Kroger API for real product pricing and availability.

## Endpoints

### 1. Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePassword123!",
  "name": "John Doe",
  "daily_calories": 2000,
  "dietary_restrictions": ["vegetarian", "gluten-free"],
  "likes": ["indian", "spicy", "savory"],
  "additional_information": "I prefer low-carb meals after 6pm",
  "macros": {
    "protein": 130.0,
    "carbs": 250.0,
    "fats": 85.0
  }
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "name": "John Doe",
    "daily_calories": 2000,
    "dietary_restrictions": ["vegetarian", "gluten-free"],
    "likes": ["indian", "spicy", "savory"]
  }
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "name": "John Doe"
  }
}
```

---

### 2. Recipe Generation

#### Generate Recipes
```http
POST /recipe
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_profile": {
    "target_macros": {
      "protein_g": 100,
      "carbs_g": 200,
      "fat_g": 50,
      "calories": 2000
    },
    "likes": ["indian", "spicy"],
    "dislikes": []
  },
  "preferences": {
    "meal_type": "dinner",
    "cuisine": "indian",
    "dietary_restrictions": "vegetarian",
    "cook_time": "30-45 mins"
  }
}
```

**Response (200 OK):**
```json
{
  "recipes": [
    {
      "title": "Spicy Paneer Tikka Masala",
      "description": "Rich and creamy Indian curry with paneer",
      "cook_time": "30 minutes",
      "prep_time": "15 minutes",
      "servings": 4,
      "macros": {
        "protein": 35.5,
        "carbs": 42.3,
        "fat": 18.7,
        "calories": 450
      },
      "ingredients": [
        {
          "name": "paneer",
          "quantity": 200,
          "unit": "g",
          "notes": "cubed"
        }
      ],
      "instructions": "## 👨‍🍳 Cooking Instructions\n\n### Step 1\n...",
      "image_url": "https://image.pollinations.ai/prompt/...",
      "cuisine": "indian",
      "difficulty": "medium",
      "tags": ["vegetarian", "high-protein"]
    }
  ],
  "message": "Generated 3 recipe options",
  "next_action": "select_recipe",
  "tools_called": ["generate_recipes_with_claude"],
  "llm_provider": "claude"
}
```

---

### 3. Grocery List Creation

#### Create Grocery List (POST /grocery)
```http
POST /grocery
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "recipe": {
    "title": "Spicy Paneer Tikka Masala",
    "ingredients": [
      {
        "name": "paneer",
        "quantity": 200,
        "unit": "g"
      }
    ]
  },
  "user_id": "user123",
  "store_preference": "Kroger"
}
```

**Response (200 OK):**
```json
{
  "agent": "GroceryAgent",
  "list_id": 42,
  "store": "Kroger",
  "items": [
    {
      "name": "Sach™ The Original Paneer",
      "quantity": "200.0 g",
      "category": "Dairy",
      "estimated_price": 8.99,
      "product_id": "0085001108803",
      "upc": null,
      "brand": "Sach"
    }
  ],
  "total_estimated_cost": 44.89,
  "kroger_items_found": 11,
  "total_items": 11,
  "message": "Created grocery list with 11 items (11/11 prices from Kroger API). Total: $44.89",
  "order_url": "https://www.kroger.com/cart?recipe=spicy-paneer-tikka-masala",
  "next_action": "review_order",
  "tools_called": ["handle_grocery_request", "create_grocery_list"],
  "llm_provider": "kroger_api"
}
```

#### Create Grocery List from Recipe (POST /grocery/from-recipe)
```http
POST /grocery/from-recipe
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Spicy Paneer Tikka Masala",
  "description": "Rich and creamy Indian curry",
  "ingredients": [
    {
      "name": "paneer",
      "quantity": 200,
      "unit": "g"
    },
    {
      "name": "quinoa",
      "quantity": 0.5,
      "unit": "cup"
    }
  ],
  "servings": 4
}
```

**Response (200 OK):**
```json
{
  "agent": "GroceryAgent",
  "list_id": 43,
  "store": "Kroger",
  "items": [
    {
      "name": "Sach™ The Original Paneer",
      "description": "Found on Kroger: Sach™ The Original Paneer",
      "quantity": 200,
      "unit": "g",
      "price_per_unit": 8.99,
      "total_price": 8.99,
      "image_url": "",
      "kroger_product_id": "0085001108803",
      "category": "groceries",
      "brand": "Sach",
      "size": "",
      "available": true,
      "source": "kroger"
    }
  ],
  "total_estimated_cost": 44.89,
  "kroger_items_found": 11,
  "total_items": 11,
  "order_url": "https://www.kroger.com/search?query=Sach™+The+Original+Paneer+Kroger®+Tri-Color+Quinoa+Kroger®+Heavy+Whipping+Cream",
  "message": "Found 11/11 items on Kroger",
  "recipe_title": "Spicy Paneer Tikka Masala",
  "llm_provider": "kroger_api"
}
```

---

### 4. Daily Meal Planning

#### Generate Daily Meals by Day
```http
POST /daily-meals/generate-by-day?day=Monday
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `day` (required): One of "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"

**Response (200 OK):**
```json
{
  "breakfast": {
    "title": "Protein Oatmeal Bowl",
    "description": "High-protein oatmeal with nuts",
    "cook_time": "10 minutes",
    "calories": 450,
    "protein": 25.0,
    "carbs": 50.0,
    "fat": 12.0,
    "ingredients": [...],
    "instructions": "..."
  },
  "lunch": {...},
  "dinner": {...},
  "total_calories": 1800,
  "total_protein": 120.0,
  "total_carbs": 180.0,
  "total_fat": 60.0,
  "macro_validation": {...}
}
```

---

### 5. User Profile

#### Get Profile
```http
GET /profile
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "name": "John Doe",
    "created_at": "2025-01-25T10:00:00Z"
  },
  "profile": {
    "daily_calories": 2000,
    "dietary_restrictions": ["vegetarian", "gluten-free"],
    "likes": ["indian", "spicy", "savory"],
    "additional_information": "I prefer low-carb meals after 6pm",
    "macros": {
      "protein": 130.0,
      "carbs": 250.0,
      "fats": 85.0
    }
  }
}
```

#### Update Profile
```http
PUT /profile
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body (all fields optional):**
```json
{
  "daily_calories": 2200,
  "dietary_restrictions": ["vegetarian"],
  "likes": ["indian", "thai", "spicy"],
  "additional_information": "Updated preferences",
  "target_protein_g": 140.0,
  "target_carbs_g": 260.0,
  "target_fat_g": 90.0
}
```

---

### 6. System Endpoints

#### Health Check
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "version": "0.3.0",
  "agents": {
    "RecipeAgent": "operational",
    "GroceryAgent": "operational"
  }
}
```

#### Root Endpoint
```http
GET /
```

**Response (200 OK):**
```json
{
  "name": "Agentic Grocery API",
  "version": "0.3.0",
  "description": "Multi-agent system for food recommendations and grocery automation",
  "features": ["Multi-Agent AI", "Claude Recipes", "Kroger Integration", "User Authentication"],
  "agents": ["RecipeAgent", "GroceryAgent"],
  "docs": "/docs",
  "health": "/health"
}
```

---

## Swift Integration Example

### Swift Networking Setup

```swift
import Foundation

struct ApiClient {
    let baseURL = "http://localhost:8000"
    var accessToken: String?
    
    func register(email: String, password: String, completion: @escaping (Result<AuthResponse, Error>) -> Void) {
        let url = URL(string: "\(baseURL)/auth/register")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "email": email,
            "username": "user_\(UUID().uuidString.prefix(8))",
            "password": password,
            "name": "Swift User",
            "daily_calories": 2000,
            "dietary_restrictions": [],
            "likes": ["indian", "spicy"]
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else { return }
            
            do {
                let authResponse = try JSONDecoder().decode(AuthResponse.self, from: data)
                completion(.success(authResponse))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    func generateRecipe(token: String, completion: @escaping (Result<RecipeResponse, Error>) -> Void) {
        let url = URL(string: "\(baseURL)/recipe")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let body: [String: Any] = [
            "user_profile": [
                "target_macros": [
                    "protein_g": 100,
                    "carbs_g": 200,
                    "fat_g": 50,
                    "calories": 2000
                ],
                "likes": ["indian", "spicy"],
                "dislikes": []
            ],
            "preferences": [
                "meal_type": "dinner",
                "cuisine": "indian",
                "dietary_restrictions": "vegetarian"
            ]
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else { return }
            
            do {
                let recipeResponse = try JSONDecoder().decode(RecipeResponse.self, from: data)
                completion(.success(recipeResponse))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    func createGroceryList(token: String, recipe: Recipe, completion: @escaping (Result<GroceryResponse, Error>) -> Void) {
        let url = URL(string: "\(baseURL)/grocery")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let body: [String: Any] = [
            "recipe": [
                "title": recipe.title,
                "ingredients": recipe.ingredients.map { [
                    "name": $0.name,
                    "quantity": $0.quantity,
                    "unit": $0.unit
                ]}
            ],
            "store_preference": "Kroger"
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else { return }
            
            do {
                let groceryResponse = try JSONDecoder().decode(GroceryResponse.self, from: data)
                completion(.success(groceryResponse))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}
```

### Swift Models

```swift
struct AuthResponse: Codable {
    let access_token: String
    let token_type: String
    let expires_in: Int
    let user: User
}

struct User: Codable {
    let id: Int
    let email: String
    let username: String
    let name: String
}

struct RecipeResponse: Codable {
    let recipes: [Recipe]
    let message: String
    let llm_provider: String
}

struct Recipe: Codable {
    let title: String
    let description: String
    let cook_time: String
    let servings: Int
    let ingredients: [Ingredient]
    let instructions: String
    let image_url: String
    let cuisine: String?
}

struct Ingredient: Codable {
    let name: String
    let quantity: Double
    let unit: String
    let notes: String?
}

struct GroceryResponse: Codable {
    let store: String
    let items: [GroceryItem]
    let total_estimated_cost: Double
    let kroger_items_found: Int
    let total_items: Int
    let message: String
}

struct GroceryItem: Codable {
    let name: String
    let quantity: String
    let category: String?
    let estimated_price: Double?
    let product_id: String?
    let brand: String?
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication token
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

Error response format:
```json
{
  "detail": "Error description here"
}
```

## Rate Limits

- No rate limits currently enforced
- Token expires after 7 days (604800 seconds)

## Notes

1. **Authentication**: All endpoints except `/auth/*`, `/health`, `/`, and `/docs` require Bearer token authentication
2. **Content-Type**: Use `application/json` for all POST/PUT requests
3. **CORS**: API supports CORS from all origins (configure for production)
4. **Kroger Integration**: Grocery lists return only products found on Kroger API (no fallback pricing)
5. **Recipe Images**: Generated using AI image generation (Pollinations.ai)

## Base URL for Production

Update the base URL when deploying:
```swift
let baseURL = "https://your-api-domain.com"
```

---

**Last Updated:** January 25, 2025  
**API Version:** 0.3.0
