#!/usr/bin/env python3
"""Test script to verify self-healing works."""

import sys
from meta_agent import MetaAgent

def test_self_healing():
    """Test if the agent can self-heal a bug."""
    print("="*70)
    print("🧪 TESTING SELF-HEALING")
    print("="*70)
    print("\n📝 Bug introduced: NameError in consulting_agent.py")
    print("   Line 216: undefined_variable_for_testing = non_existent_variable")
    print("\n🔍 Testing if agent can detect and fix this bug...\n")
    
    meta_agent = MetaAgent()
    
    # This should trigger the bug and self-healing
    result = meta_agent.process_request("whats my macbook battery status currently")
    
    print("\n" + "="*70)
    print("📊 RESULT")
    print("="*70)
    print(f"Status: {result.get('status')}")
    
    if result.get('self_healed'):
        print("✅ SELF-HEALING SUCCESSFUL!")
        print(f"Healing details: {result.get('healing_details')}")
    else:
        print("❌ Self-healing did not trigger or succeed")
        print(f"Message: {result.get('message', 'N/A')}")
    
    return result.get('status') == 'success' and result.get('self_healed', False)

if __name__ == "__main__":
    success = test_self_healing()
    sys.exit(0 if success else 1)

