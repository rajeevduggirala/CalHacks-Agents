# 📱 Mobile App Integration Guide

## Overview

Your **Agentic Grocery** API is now production-ready for mobile app consumption with:
- ✅ **JWT Authentication** (7-day token expiry)
- ✅ **SQLite Database** (user accounts, profiles, saved recipes, grocery lists)
- ✅ **Authenticated Endpoints** (all agent endpoints require login)
- ✅ **Claude AI Integration** (real recipe generation)
- ✅ **Kroger API Integration** (real grocery pricing)

---

## 🏗️ Architecture

```
Mobile App (React Native/Flutter/Swift)
    ↓ (HTTP/REST with JWT)
FastAPI Backend (main.py)
    ├── Authentication (JWT tokens)
    ├── SQLite Database
    ├── ChatAgent (conversational AI)
    ├── RecipeAgent (Claude-powered)
    └── GroceryAgent (Kroger-integrated)
```

---

## 🔐 Authentication Flow

### 1. User Registration
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "john_doe"
  }
}
```

### 2. User Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** Same as registration

### 3. Authenticated Requests
All subsequent requests must include the JWT token:

```http
GET /profile
Authorization: Bearer eyJhbGc...
```

---

## 📱 Mobile App Endpoints

### User Profile Management

#### Get Profile
```http
GET /profile
Authorization: Bearer {token}
```

#### Update Profile
```http
PUT /profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "height_cm": 175,
  "weight_kg": 70,
  "goal": "cut",
  "diet": "vegetarian",
  "workout_frequency": "5/week",
  "likes": ["spicy", "south indian"],
  "dislikes": ["mushrooms"],
  "target_protein_g": 140,
  "target_carbs_g": 200,
  "target_fat_g": 50,
  "target_calories": 1800
}
```

### Agent Interactions

#### Chat with AI
```http
POST /chat
Authorization: Bearer {token}
Content-Type: application/json

{
  "message": "I want a high protein vegetarian dinner"
}
```

#### Generate Recipes
```http
POST /recipe
Authorization: Bearer {token}
Content-Type: application/json

{
  "preferences": {
    "meal_type": "dinner",
    "cook_time": "30-45 mins",
    "cuisine": "indian"
  }
}
```

**Note:** User profile is automatically loaded from database!

#### Create Grocery List
```http
POST /grocery
Authorization: Bearer {token}
Content-Type: application/json

{
  "recipe": {
    "title": "Paneer Tikka",
    "ingredients": [
      {"name": "paneer", "quantity": "200g"}
    ]
  },
  "store_preference": "Kroger"
}
```

### Recipe Management

#### Get Saved Recipes
```http
GET /recipes
Authorization: Bearer {token}
```

#### Save Recipe
```http
POST /recipes/save
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Paneer Tikka with Quinoa",
  "description": "High protein vegetarian meal",
  "cook_time": "30 mins",
  "servings": 1,
  "cuisine": "Indian",
  "difficulty": "medium",
  "protein_g": 49,
  "carbs_g": 70,
  "fat_g": 15,
  "calories": 540,
  "fiber_g": 8,
  "ingredients": [...],
  "instructions": [...],
  "image_url": "https://..."
}
```

#### Toggle Favorite
```http
POST /recipes/{recipe_id}/favorite
Authorization: Bearer {token}
```

### Grocery Lists

#### Get All Grocery Lists
```http
GET /grocery-lists
Authorization: Bearer {token}
```

#### Mark List as Completed
```http
POST /grocery-lists/{list_id}/complete
Authorization: Bearer {token}
```

### Meal Logging

#### Log a Meal
```http
POST /meals/log
Authorization: Bearer {token}
Content-Type: application/json

{
  "meal_type": "dinner",
  "recipe_title": "Paneer Tikka",
  "protein_g": 49,
  "carbs_g": 70,
  "fat_g": 15,
  "calories": 540,
  "rating": 5,
  "notes": "Delicious!"
}
```

#### Get Meal History
```http
GET /meals/history?days=7
Authorization: Bearer {token}
```

### User Stats
```http
GET /stats
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_recipes": 15,
  "favorite_recipes": 5,
  "total_grocery_lists": 8,
  "total_meals_logged": 42
}
```

---

## 📊 Database Schema

### Users Table
- id, email, username, hashed_password, is_active, created_at, updated_at

### User Profiles Table
- id, user_id, height_cm, weight_kg, age, gender, goal, diet, allergies, likes, dislikes, target macros

### Saved Recipes Table
- id, user_id, title, description, cook_time, servings, macros, ingredients, instructions, is_favorite, times_cooked

### Grocery Lists Table
- id, user_id, recipe_id, name, store, total_cost, items, is_completed, completed_at

### Meal History Table
- id, user_id, recipe_id, date, meal_type, recipe_title, macros, rating, notes

---

## 🎨 Mobile App Features to Implement

### Authentication Screen
- Login form
- Registration form
- Password validation
- Token storage (SecureStore/KeyChain)
- Auto-login if token valid

### Profile Setup
- Onboarding flow for new users
- Height/weight input
- Goal selection (cut/bulk/maintain)
- Dietary preferences
- Food likes/dislikes
- Macro targets

### Home Dashboard
- User stats
- Recent recipes
- Today's meal plan
- Quick actions

### Recipe Discovery
- Chat interface with AI
- Recipe generation with filters
- Swipe cards for recipe selection
- Save/favorite buttons
- View detailed recipe

### Grocery Shopping
- Auto-generate list from recipe
- Real-time Kroger prices
- Checkoff items
- Store selection
- Order button (Kroger link)

### Meal Tracker
- Log daily meals
- View nutrition breakdown
- Progress towards goals
- Calendar view
- Rating system

---

## 🔧 Mobile SDK Example (React Native)

```javascript
// api.js
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE_URL = 'https://your-api.com'; // Or localhost for dev

class AgenticGroceryAPI {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Add auth token to requests
    this.client.interceptors.request.use(async (config) => {
      const token = await SecureStore.getItemAsync('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }
  
  // Auth
  async register(email, username, password) {
    const response = await this.client.post('/auth/register', {
      email, username, password
    });
    await SecureStore.setItemAsync('auth_token', response.data.access_token);
    return response.data;
  }
  
  async login(email, password) {
    const response = await this.client.post('/auth/login', {
      email, password
    });
    await SecureStore.setItemAsync('auth_token', response.data.access_token);
    return response.data;
  }
  
  async logout() {
    await SecureStore.deleteItemAsync('auth_token');
  }
  
  // Profile
  async getProfile() {
    const response = await this.client.get('/profile');
    return response.data;
  }
  
  async updateProfile(profileData) {
    const response = await this.client.put('/profile', profileData);
    return response.data;
  }
  
  // Chat
  async chat(message) {
    const response = await this.client.post('/chat', { message });
    return response.data;
  }
  
  // Recipes
  async generateRecipes(preferences) {
    const response = await this.client.post('/recipe', { preferences });
    return response.data;
  }
  
  async getSavedRecipes() {
    const response = await this.client.get('/recipes');
    return response.data;
  }
  
  async saveRecipe(recipe) {
    const response = await this.client.post('/recipes/save', recipe);
    return response.data;
  }
  
  async toggleFavorite(recipeId) {
    const response = await this.client.post(`/recipes/${recipeId}/favorite`);
    return response.data;
  }
  
  // Grocery
  async createGroceryList(recipe, store = 'Kroger') {
    const response = await this.client.post('/grocery', {
      recipe,
      store_preference: store
    });
    return response.data;
  }
  
  async getGroceryLists() {
    const response = await this.client.get('/grocery-lists');
    return response.data;
  }
  
  // Meals
  async logMeal(mealData) {
    const response = await this.client.post('/meals/log', mealData);
    return response.data;
  }
  
  async getMealHistory(days = 7) {
    const response = await this.client.get(`/meals/history?days=${days}`);
    return response.data;
  }
  
  // Stats
  async getStats() {
    const response = await this.client.get('/stats');
    return response.data;
  }
}

export default new AgenticGroceryAPI();
```

### Usage Example
```javascript
import api from './api';

// Register
const user = await api.register('user@example.com', 'john_doe', 'password123');

// Get recipes
const recipes = await api.generateRecipes({
  meal_type: 'dinner',
  cook_time: '30 mins',
  cuisine: 'indian'
});

// Create grocery list
const groceryList = await api.createGroceryList(recipes.recipes[0]);
```

---

## 🚀 Deployment Recommendations

### Option 1: Railway (Easiest)
```bash
# Install Railway CLI
npm install -g railway

# Login and init
railway login
railway init

# Deploy
railway up
```

### Option 2: AWS/GCP
- Use EC2/Compute Engine
- Setup nginx reverse proxy
- SSL with Let's Encrypt
- PM2 for process management

### Option 3: Fly.io
```bash
flyctl launch
flyctl deploy
```

---

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit `.env` to git
   - Use different keys for dev/production
   - Rotate JWT secret regularly

2. **HTTPS Only**
   - Always use HTTPS in production
   - HTTP is OK for localhost dev

3. **Token Storage**
   - Mobile: Use SecureStore/KeyChain
   - Never store in AsyncStorage

4. **Password Requirements**
   - Minimum 8 characters
   - Mix of letters, numbers, symbols
   - Use bcrypt for hashing (already implemented)

5. **Rate Limiting**
   - Add rate limiting middleware
   - Prevent brute force attacks

---

## 📈 Monitoring & Analytics

Consider adding:
- Sentry for error tracking
- Mixpanel/Amplitude for user analytics
- LogRocket for session replay
- Stripe for monetization

---

## 🎯 Next Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   ```bash
   python database.py
   ```

3. **Start Server**
   ```bash
   python main.py
   ```

4. **Test with Mobile App**
   - Use Postman/Insomnia first
   - Then integrate with mobile SDK

5. **Deploy to Production**
   - Choose hosting provider
   - Set up CI/CD
   - Configure domain

---

Your API is ready for production mobile app integration! 🎉

