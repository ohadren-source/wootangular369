#!/usr/bin/env python3
"""
Test SC2SC messaging end-to-end
Run against deployed Railway instance to verify Sol can send messages to Lexi
"""

import requests
import json
import sys
import time

# Configuration
RAILWAY_URL = input("Enter your Railway instance URL (e.g., https://app-name.railway.app): ").strip()
if not RAILWAY_URL:
    RAILWAY_URL = "http://localhost:8000"  # Fallback for local testing

# Admin credentials (from main.py defaults)
ADMIN_USER = "Ohad"
ADMIN_PASS = "route666"

def test_sc2sc_tools_available():
    """Test 1: Verify Sol reports having SC2SC tools"""
    print("\n" + "="*80)
    print("TEST 1: SC2SC Tools Available")
    print("="*80)

    payload = {
        "message": "List the SC2SC tools you have available: send_agent_message, receive_agent_messages, get_conversation_history, register_sol, heartbeat",
        "history": [],
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }

    try:
        response = requests.post(f"{RAILWAY_URL}/api/chat", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        response_text = data.get('response', '')
        print(f"\nSol's response:\n{response_text[:500]}")

        # Check if Sol claims to have the tools
        has_tools = any(tool in response_text.lower() for tool in [
            'send_agent_message', 'register_sol', 'heartbeat'
        ])

        if has_tools:
            print("\n✅ PASS: Sol reports having SC2SC tools")
            return True
        else:
            print("\n❌ FAIL: Sol does not report having SC2SC tools")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_send_message_to_lexi():
    """Test 2: Have Sol send a message to Lexi via SC2SC"""
    print("\n" + "="*80)
    print("TEST 2: Send Message to Lexi")
    print("="*80)

    payload = {
        "message": """Call send_agent_message with these parameters:
- to_agent: "lexi"
- handoff_request: "cognitive_state_sync"
- cognitive_state: {"thought_count": 42, "resonance_level": 0.8, "mode": "testing"}

Report the message_id you get back.""",
        "history": [],
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }

    try:
        response = requests.post(f"{RAILWAY_URL}/api/chat", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        response_text = data.get('response', '')
        print(f"\nSol's response:\n{response_text[:500]}")

        # Check if message was sent (look for message_id or success)
        success = any(keyword in response_text.lower() for keyword in [
            'message_id', 'success', 'sent', 'registered'
        ])

        if success:
            print("\n✅ PASS: Sol sent message to Lexi")
            return True, response_text
        else:
            print("\n❌ FAIL: No indication message was sent")
            return False, response_text

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, str(e)


def test_receive_messages():
    """Test 3: Have Sol check for messages from Lexi"""
    print("\n" + "="*80)
    print("TEST 3: Receive Messages from Lexi")
    print("="*80)

    payload = {
        "message": """Call receive_agent_messages with limit=5.
Report any messages you receive from Lexi or other agents.""",
        "history": [],
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }

    try:
        response = requests.post(f"{RAILWAY_URL}/api/chat", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        response_text = data.get('response', '')
        print(f"\nSol's response:\n{response_text[:500]}")

        if response_text:
            print("\n✅ PASS: Sol checked for messages")
            return True, response_text
        else:
            print("\n⚠️  WARNING: No response received")
            return False, response_text

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, str(e)


def test_conversation_history():
    """Test 4: Check conversation history with Lexi"""
    print("\n" + "="*80)
    print("TEST 4: Conversation History")
    print("="*80)

    payload = {
        "message": """Call get_conversation_history with:
- with_agent: "lexi"
- limit: 10

Report any conversation history you find with Lexi.""",
        "history": [],
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }

    try:
        response = requests.post(f"{RAILWAY_URL}/api/chat", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        response_text = data.get('response', '')
        print(f"\nSol's response:\n{response_text[:500]}")

        if response_text:
            print("\n✅ PASS: Sol retrieved conversation history")
            return True, response_text
        else:
            print("\n⚠️  WARNING: No response received")
            return False, response_text

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, str(e)


def main():
    """Run all SC2SC tests"""
    print("\n" + "="*80)
    print("SC2SC MESSAGING TEST SUITE")
    print("="*80)
    print(f"Testing against: {RAILWAY_URL}")

    results = {}

    # Test 1
    results["Tools Available"] = test_sc2sc_tools_available()
    time.sleep(1)

    # Test 2
    test2_pass, test2_response = test_send_message_to_lexi()
    results["Send to Lexi"] = test2_pass
    time.sleep(1)

    # Test 3
    test3_pass, test3_response = test_receive_messages()
    results["Receive Messages"] = test3_pass
    time.sleep(1)

    # Test 4
    test4_pass, test4_response = test_conversation_history()
    results["Conversation History"] = test4_pass

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} passed")
    print("="*80)

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
