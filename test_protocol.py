"""
Quick test to verify Chat Protocol v0.3.0 implementation
"""
import sys
import importlib.util

def test_agent_protocol(agent_path, agent_name):
    """Test if an agent has Chat Protocol v0.3.0 properly implemented"""
    print(f"\n{'='*60}")
    print(f"Testing {agent_name}")
    print('='*60)
    
    try:
        # Import the agent module
        spec = importlib.util.spec_from_file_location(agent_name.lower(), agent_path)
        module = importlib.util.module_from_spec(spec)
        
        # Check for Protocol import
        with open(agent_path, 'r') as f:
            content = f.read()
            
        checks = {
            "Protocol import": "from uagents import Agent, Context, Model, Protocol" in content,
            "Protocol creation": 'Protocol("chat", version="0.3.0")' in content,
            "Protocol handler": "@" in content and "protocol.on_message" in content,
            "Protocol inclusion": "agent.include(" in content and "protocol)" in content,
            "Protocol logging": "[Chat Protocol v0.3.0]" in content,
        }
        
        print(f"\n✅ {agent_name} Protocol Checks:")
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {check}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            print(f"\n🎉 {agent_name} is fully Chat Protocol v0.3.0 compliant!")
        else:
            print(f"\n⚠️  {agent_name} is missing some protocol requirements")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing {agent_name}: {e}")
        return False


def main():
    """Test all agents"""
    print("="*60)
    print("Chat Protocol v0.3.0 Compliance Test")
    print("="*60)
    
    agents = [
        ("agents/chat_agent/agent.py", "ChatAgent"),
        ("agents/recipe_agent/agent.py", "RecipeAgent"),
        ("agents/grocery_agent/agent.py", "GroceryAgent"),
    ]
    
    results = []
    for agent_path, agent_name in agents:
        passed = test_agent_protocol(agent_path, agent_name)
        results.append((agent_name, passed))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for agent_name, passed in results:
        status = "✅ COMPLIANT" if passed else "❌ NON-COMPLIANT"
        print(f"{status}: {agent_name}")
    
    all_compliant = all(passed for _, passed in results)
    
    if all_compliant:
        print("\n🎉🎉🎉 ALL AGENTS ARE CHAT PROTOCOL v0.3.0 COMPLIANT! 🎉🎉🎉")
        print("\n✅ Your agents are ready for:")
        print("   - ASI:One integration")
        print("   - Agentverse deployment")
        print("   - Agent-to-agent communication")
        print("\n📡 Next steps:")
        print("   1. Set up environment variables in .env")
        print("   2. Run agents: python agents/chat_agent/agent.py")
        print("   3. Register on Agentverse: https://agentverse.ai")
        return 0
    else:
        print("\n⚠️  Some agents are not fully compliant. Review the checks above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

