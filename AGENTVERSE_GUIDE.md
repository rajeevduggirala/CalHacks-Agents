# 🚀 Agentverse Registration Guide

Complete guide to registering your Agentic Grocery agents on **Agentverse** and making them discoverable via **ASI:One**.

Based on [Agentverse Documentation](https://docs.agentverse.ai/documentation/getting-started/overview) and [uAgents Framework](https://uagents.fetch.ai/docs).

---

## 📋 Overview

Your Agentic Grocery project has **3 specialized agents** ready for Agentverse:

1. **ChatAgent** (`@agentic-grocery-chat`) - Conversational coordinator
2. **RecipeAgent** (`@agentic-grocery-recipes`) - Recipe generator with Claude AI
3. **GroceryAgent** (`@agentic-grocery-shopping`) - Grocery list builder with Kroger API

All agents are built with the **uAgents Framework** and follow the **Chat Protocol v0.3.0** for ASI:One compatibility.

---

## 🎯 Registration Methods

You have 3 options to connect your agents to Agentverse:

### Option 1: Hosted Agents (Easiest)
Create agents directly on Agentverse platform.

### Option 2: Mailbox (Recommended for Local Agents)
Connect locally running agents via Mailbox for remote access.

### Option 3: Proxy
Use the Proxy service for agent communication.

**For this project, we recommend Option 2 (Mailbox)** since your agents are already built and running locally.

---

## 🔧 Step-by-Step Registration

### Step 1: Get Your Agent Metadata

Start your API server:
```bash
python main.py
```

Get agent metadata:
```bash
curl http://localhost:8000/agents-metadata
```

This returns metadata for all 3 agents including:
- Agent names and custom @handles
- Descriptions optimized for search
- Tags for discoverability
- Endpoints and capabilities

### Step 2: Register on Agentverse

1. **Visit Agentverse**
   - Go to https://agentverse.ai
   - Sign up or log in

2. **Create New Agent** (for each of the 3 agents)
   - Click "Create Agent" or "Launch Agent"
   - Choose appropriate method (Hosted, Mailbox, or Proxy)

3. **Configure Agent Details**

#### For ChatAgent:
- **Name**: `ChatAgent` or `Agentic Grocery Chat`
- **Handle**: `@agentic-grocery-chat`
- **Description**: 
  ```
  Conversational entrypoint for Agentic Grocery - handles user queries, 
  extracts dietary preferences, and coordinates with other agents to provide 
  personalized meal planning and grocery automation.
  ```
- **Tags**: `nutrition, recipes, fetchai, agentic-ai, chatbot, conversation`
- **Endpoint**: `http://localhost:8000/chat` (or your deployed URL)
- **Protocol**: Chat Protocol v0.3.0

#### For RecipeAgent:
- **Name**: `RecipeAgent` or `Agentic Grocery Recipes`
- **Handle**: `@agentic-grocery-recipes`
- **Description**: 
  ```
  Intelligent recipe generator powered by Claude AI that creates personalized 
  meal options based on user preferences, dietary goals, and macro requirements. 
  Generates detailed recipes with ingredients, instructions, and nutritional info.
  ```
- **Tags**: `nutrition, recipes, meal-planning, fetchai, agentic-ai, claude, ai-powered`
- **Endpoint**: `http://localhost:8000/recipe`
- **Protocol**: Chat Protocol v0.3.0

#### For GroceryAgent:
- **Name**: `GroceryAgent` or `Agentic Grocery Shopping`
- **Handle**: `@agentic-grocery-shopping`
- **Description**: 
  ```
  Automated grocery list builder that extracts ingredients from recipes and 
  uses Kroger API for real product pricing and availability. Creates formatted 
  shopping lists ready for ordering.
  ```
- **Tags**: `grocery, shopping, kroger, fetchai, agentic-ai, automation, e-commerce`
- **Endpoint**: `http://localhost:8000/grocery`
- **Protocol**: Chat Protocol v0.3.0

### Step 3: Add Custom Agent Avatars

According to Agentverse best practices, agents with custom avatars rank higher!

1. Create or design logos for each agent:
   - ChatAgent: Chat bubble or conversation icon
   - RecipeAgent: Chef hat or recipe book icon
   - GroceryAgent: Shopping cart or grocery bag icon

2. Upload via Agentverse UI in agent settings

### Step 4: Write Search-Optimized READMEs

Each agent should have a comprehensive README following these guidelines:

#### README Structure:
```markdown
# [Agent Name]

## Overview
[Clear description of what the agent does]

## Capabilities
- Capability 1
- Capability 2
- Capability 3

## Use Cases
### Use Case 1: [Name]
[Description and example]

### Use Case 2: [Name]
[Description and example]

## How to Interact
[Explain how users can communicate with the agent]

## Example Queries
- "Query example 1"
- "Query example 2"

## Limitations
[What the agent does NOT do]

## Technical Details
- Framework: Fetch.ai uAgents
- Protocol: Chat Protocol v0.3.0
- Integrations: [List APIs used]
```

### Step 5: Optimize for Ranking

According to [Agentverse ranking criteria](https://docs.agentverse.ai/documentation/getting-started/overview), improve your score with:

#### ✅ Must-Haves:
- [x] **README quality** - Clear, detailed, keyword-rich
- [x] **Protocol support** - Chat Protocol v0.3.0 ✓
- [x] **Custom @handles** - Already configured ✓
- [x] **Rich metadata** - Tags, descriptions ✓
- [x] **Agent avatars** - Upload custom images

#### 🚀 Boost Visibility:
- [ ] **Domain association** - Register with a verified domain
- [ ] **Mainnet registration** - Deploy to ASI Mainnet
- [ ] **Verification** - Get verified badge
- [ ] **Interaction metrics** - Encourage usage
- [ ] **Active status** - Keep agents online and responsive

---

## 💡 Using Mailbox for Local Agents

Since your agents run locally, use **Mailbox** to make them accessible remotely:

### 1. Update Agent Code

Add mailbox configuration to each agent:

```python
from uagents import Agent

agent = Agent(
    name="ChatAgent",
    seed="your-seed",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
    mailbox="YOUR_MAILBOX_KEY_FROM_AGENTVERSE"  # Add this
)
```

### 2. Get Mailbox Key

1. In Agentverse, create a new agent
2. Select "Mailbox" option
3. Copy the mailbox key provided
4. Add to your `.env` file:
   ```bash
   AGENTVERSE_MAILBOX_KEY=your_mailbox_key_here
   ```

### 3. Update Agent Configuration

In each agent file, load from environment:

```python
import os
from dotenv import load_dotenv

load_dotenv()

agent = Agent(
    name="ChatAgent",
    seed=os.getenv("CHAT_AGENT_SEED"),
    mailbox=os.getenv("AGENTVERSE_MAILBOX_KEY")
)
```

---

## 🧪 Testing on ASI:One

Once registered, test your agents on ASI:One:

### 1. Visit ASI:One
Go to https://asi1.ai/chat

### 2. Search for Your Agents

Try these queries:
- "Find @agentic-grocery-chat"
- "I need help planning a vegetarian meal"
- "Show me agents that can generate recipes"
- "Find grocery shopping automation agents"

### 3. Interact with Agents

Use your custom handles directly:
```
@agentic-grocery-chat I want a high protein vegetarian dinner
```

```
@agentic-grocery-recipes Generate lunch ideas for weight loss
```

```
@agentic-grocery-shopping Create a grocery list for my recipe
```

---

## 📊 Monitoring Performance

### Ranking & Analytics Dashboard

Each agent has a dashboard on Agentverse showing:
- **Interactions** - How many times your agent was called
- **Searches** - How often it appears in search results
- **Top search terms** - What queries lead to your agent
- **Ranking score** - Overall visibility score

### Improve Your Ranking

Track these metrics and optimize:

1. **If low search results**:
   - Add more relevant keywords to README
   - Improve description clarity
   - Add more use case examples

2. **If low interactions**:
   - Make README more actionable
   - Add clear example queries
   - Improve response quality

3. **If low ranking**:
   - Upload custom avatar
   - Add domain verification
   - Deploy to Mainnet
   - Keep agents active

---

## 🎯 Best Practices from Agentverse

### ✅ DO:

- **Use descriptive names** under 20 characters
- **Write clear descriptions** focused on capabilities
- **Add relevant tags** that users might search for
- **Keep agents active** and responsive
- **Update regularly** based on usage patterns
- **Encourage feedback** to improve ranking
- **Use custom @handles** for easy discovery
- **Upload agent avatars** for visual recognition

### ❌ DON'T:

- Use generic names like "MyAgent" or "Bot1"
- Stuff names with keywords (use README for that)
- Add location in agent name (use metadata instead)
- Use overly long names (they get truncated in UI)
- Leave agents inactive for long periods
- Ignore user feedback and interaction metrics

---

## 🚀 Deployment Checklist

Before going live:

- [ ] All 3 agents registered on Agentverse
- [ ] Custom @handles set for each agent
- [ ] READMEs written and uploaded
- [ ] Custom avatars uploaded
- [ ] Mailbox keys configured (if using local agents)
- [ ] Agents tested on ASI:One
- [ ] Tags optimized for search
- [ ] Descriptions clear and keyword-rich
- [ ] Example queries documented
- [ ] Monitoring dashboard reviewed

---

## 📚 Additional Resources

- [Agentverse Overview](https://docs.agentverse.ai/documentation/getting-started/overview)
- [uAgents Documentation](https://uagents.fetch.ai/docs)
- [Chat Protocol Integration](https://docs.agentverse.ai/documentation/launch-agents/connect-your-agents-chat-protocol-integration)
- [Agent Search Optimization](https://docs.agentverse.ai/documentation/search-for-agents/agent-search-optimization)
- [ASI:One Platform](https://asi1.ai/chat)

---

## 🤝 Support

If you encounter issues:

1. Check Agentverse documentation
2. Review agent logs in dashboard
3. Test endpoints directly via `/docs`
4. Verify Chat Protocol implementation
5. Join Fetch.ai community for help

---

**Ready to make your agents discoverable!** 🎉

Your agents are already ASI:One compatible and following best practices. Just register them on Agentverse and start tracking interactions!

