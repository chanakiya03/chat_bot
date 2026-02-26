
import os
import sys
import json
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock Groq client before importing other modules
import chatbot.engine.groq_client as groq_client
groq_client.ask_groq_json = MagicMock(return_value=json.dumps({
    "intent": "greeting",
    "raw_colleges": [],
    "raw_courses": [],
    "is_comparison": False
}))

from chatbot.engine.router import analyze_query_advanced, QueryAnalysis
from chatbot.engine.responder import generate_response

def test_greeting_logic():
    print("--- Testing Greeting Logic ---")
    query = "hi"
    
    # 1. Test Router
    analysis = analyze_query_advanced(query, [])
    print(f"Detected Intent: {analysis.intent}")
    assert analysis.intent == "greeting"
    
    # 2. Test Orchestrator
    response = generate_response(query, [])
    print(f"Response Text: {response['text']}")
    print(f"Intent: {response['intent']}")
    
    assert response['intent'] == "greeting"
    assert "Hello! 👋 I am CollegeBot" in response['text']
    assert "suggestions" in response
    print("Greeting logic verified successfully!")

if __name__ == "__main__":
    try:
        test_greeting_logic()
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
