
import os
import sys
import json
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock Groq client
import chatbot.engine.groq_client as groq_client
groq_client.ask_groq_json = MagicMock(return_value=json.dumps({
    "intent": "facility",
    "raw_colleges": ["WCC"],
    "raw_courses": [],
    "is_comparison": False
}))

from chatbot.engine.router import analyze_query_advanced
from chatbot.engine.responder import generate_response

def test_wcc_facility():
    print("--- Testing WCC Facility Logic ---")
    query = "Does WCC have a Commerce Association?"
    
    # 1. Test Router & Fuzzy Mapping
    analysis = analyze_query_advanced(query, [])
    from chatbot.engine.router import extract_colleges_fuzzy
    college_keys = extract_colleges_fuzzy(analysis.raw_colleges)
    
    print(f"Extracted Keys: {college_keys}")
    assert "womens-christian-college" in college_keys
    
    # 2. Test Handler/Orchestrator
    response = generate_response(query, [])
    print(f"Response Text: {response['text'][:150]}...")
    print(f"Intent: {response['intent']}")
    
    assert response['intent'] == "facility"
    assert "Women’s Christian College" in response['text']
    assert "Commerce Association" in response['text']
    print("WCC Facility logic verified successfully!")

if __name__ == "__main__":
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3'}},
                INSTALLED_APPS=['chatbot'],
            )
        import django
        django.setup()
        
        test_wcc_facility()
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
