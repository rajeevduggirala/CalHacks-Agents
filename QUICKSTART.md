# 🚀 Quick Start Guide - Agentic Grocery

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment (Optional)

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your API keys (optional for basic functionality)
# The system works with mock data by default
```

### 3. Start the Server

```bash
python main.py
```

You should see:
```
🚀 Starting Agentic Grocery API on 0.0.0.0:8000
📚 API Documentation: http://localhost:8000/docs
🔍 Alternative docs: http://localhost:8000/redoc
```

### 4. Test the API

Open your browser and visit:
- **API Docs**: http://localhost:8000/docs (interactive Swagger UI)
- **Health Check**: http://localhost:8000/health

## 📋 Example API Calls

### Using cURL

#### 1. Chat Endpoint
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a high protein vegetarian dinner, quick to make",
    "user_id": "raj"
  }'
```

#### 2. Recipe Endpoint
```bash
curl -X POST "http://localhost:8000/recipe" \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "height_cm": 175,
      "weight_kg": 70,
      "goal": "cut",
      "diet": "vegetarian"
    },
    "preferences": {
      "meal_type": "dinner",
      "cook_time": "30-45 mins",
      "cuisine": "indian"
    }
  }'
```

#### 3. Grocery Endpoint
```bash
curl -X POST "http://localhost:8000/grocery" \
  -H "Content-Type: application/json" \
  -d '{
    "recipe": {
      "title": "Paneer Tikka with Quinoa",
      "ingredients": [
        {"name": "paneer", "quantity": "200g"},
        {"name": "quinoa", "quantity": "1/2 cup"},
        {"name": "yogurt", "quantity": "1/4 cup"}
      ]
    },
    "user_id": "raj",
    "store_preference": "Instacart"
  }'
```

#### 4. Full Flow (All-in-One)
```bash
curl -X POST "http://localhost:8000/full-flow" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a high protein vegetarian lunch that takes 30 minutes",
    "user_id": "raj"
  }'
```

### Using Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Full flow example
response = requests.post(
    f"{BASE_URL}/full-flow",
    json={
        "message": "I want a high protein vegetarian dinner, quick to make",
        "user_id": "raj"
    }
)

result = response.json()
print("Chat Response:", result['chat_response'])
print("Recipes:", len(result['recipe_response']['recipes']))
print("Grocery List:", result['grocery_response']['message'])
```

### Using the Interactive Docs

1. Visit http://localhost:8000/docs
2. Click on any endpoint (e.g., `/full-flow`)
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"
6. View the response below

## 🧪 Test Different Scenarios

### Scenario 1: Quick Breakfast
```json
{
  "message": "I need a quick breakfast with 30g protein, I'm vegetarian",
  "user_id": "raj"
}
```

### Scenario 2: Specific Cuisine
```json
{
  "message": "I want an Italian lunch with lots of vegetables",
  "user_id": "raj"
}
```

### Scenario 3: Time Constrained
```json
{
  "message": "Give me a 15 minute dinner recipe",
  "user_id": "raj"
}
```

### Scenario 4: Incomplete Request
```json
{
  "message": "I'm hungry",
  "user_id": "raj"
}
```
*The system will ask for more details!*

## 🔧 Customizing User Profile

Edit `data/user_profile.json` to customize dietary preferences:

```json
{
  "user": "your_name",
  "height_cm": 180,
  "weight_kg": 75,
  "goal": "bulk",  // Options: cut, bulk, maintain
  "diet": "vegan",  // Options: vegetarian, vegan, omnivore
  "workout_frequency": "6/week",
  "likes": ["spicy", "mediterranean"],
  "dislikes": ["onions"],
  "target_macros": {
    "protein_g": 150,
    "carbs_g": 250,
    "fat_g": 60,
    "calories": 2200
  }
}
```

## 🤖 Running Individual Agents

You can also run agents independently:

```bash
# Terminal 1 - ChatAgent
python agents/chat_agent/agent.py

# Terminal 2 - RecipeAgent  
python agents/recipe_agent/agent.py

# Terminal 3 - GroceryAgent
python agents/grocery_agent/agent.py
```

## 📊 Understanding the Response Structure

### Chat Response
```json
{
  "agent": "ChatAgent",
  "message": "Great! Let me find some recipes for you...",
  "next_action": "generate_recipes",
  "structured_data": {
    "user_profile": {...},
    "preferences": {...}
  }
}
```

### Recipe Response
```json
{
  "agent": "RecipeAgent",
  "recipes": [
    {
      "title": "Paneer Tikka with Quinoa",
      "description": "Grilled cottage cheese...",
      "cook_time": "30-45 mins",
      "macros": {
        "protein_g": 49,
        "carbs_g": 70,
        "fat_g": 15,
        "calories": 540
      },
      "ingredients": [...],
      "instructions": [...]
    }
  ],
  "message": "Here are 3 personalized recipe options for you!",
  "next_action": "select_recipe"
}
```

### Grocery Response
```json
{
  "agent": "GroceryAgent",
  "store": "Instacart",
  "items": [
    {
      "name": "paneer",
      "quantity": "200g",
      "category": "Dairy",
      "estimated_price": 4.99
    }
  ],
  "total_estimated_cost": 32.45,
  "order_url": "https://instacart.com/order/raj/...",
  "next_action": "review_order"
}
```

## 🌐 Registering on Agentverse

1. **Get Agent Configuration**
```bash
curl http://localhost:8000/agent-config
```

2. **Visit Agentverse**
   - Go to https://agentverse.ai
   - Sign up / Login
   - Click "Create Agent"

3. **Register Each Agent**
   - Use the configuration from `/agent-config`
   - Add appropriate tags
   - Set the endpoint URL

4. **Test on ASI:One**
   - Visit https://asi1.ai/chat
   - Search for your agent by name or tags
   - Test interactions

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
python main.py  # Edit main.py to change PORT
```

### Import Errors
```bash
# Make sure you're in the project root directory
cd /path/to/agentic-grocery

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### No Recipes Generated
- Check that user profile exists in `data/user_profile.json`
- Ensure the request has required fields (meal_type, cook_time)
- Check API logs for errors

## 📚 Next Steps

1. ✅ Test all API endpoints
2. ✅ Customize your user profile
3. ✅ Register agents on Agentverse
4. ✅ Try the ASI:One sandbox
5. ✅ Add OpenAI integration for better recipes
6. ✅ Build a frontend interface

## 💡 Tips

- Use the `/full-flow` endpoint for quick testing
- Check `/health` to ensure all agents are operational
- Use the interactive docs at `/docs` for easy testing
- Monitor logs in the terminal for debugging
- Start with simple queries and build up complexity

Happy coding! 🚀

