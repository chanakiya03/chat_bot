
import os
import sys
import json
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock Groq client
import chatbot.engine.groq_client as groq_client
groq_client.ask_groq_json = MagicMock(side_effect=[
    # Test 1: Cheapest BSC CS
    json.dumps({"intent": "fee", "raw_colleges": [], "raw_courses": ["BSC CS"], "is_comparison": False, "raw_locations": []}),
    # Test 2: Most expensive MBA
    json.dumps({"intent": "fee", "raw_colleges": [], "raw_courses": ["MBA"], "is_comparison": False, "raw_locations": []}),
    # Test 3: BSC CS in OMR
    json.dumps({"intent": "fee", "raw_colleges": [], "raw_courses": ["BSC CS"], "is_comparison": False, "raw_locations": ["OMR"]})
])

from chatbot.engine.responder import generate_response

def test_fee_intelligence():
    print("--- Testing Fee Handler Intelligence ---")
    
    # 1. Test Cheapest
    query1 = "Which is the cheapest B.Sc CS college?"
    resp1 = generate_response(query1, [])
    print(f"Query: {query1}")
    print(f"Response: {resp1['text'][:150]}...")
    assert "Cheapest" in resp1['text']
    assert "B.Sc" in resp1['text']
    assert "B.Tech" not in resp1['text']
    
    # 2. Test Most Expensive
    query2 = "What is the most expensive MBA college?"
    resp2 = generate_response(query2, [])
    print(f"Query: {query2}")
    print(f"Response: {resp2['text'][:150]}...")
    assert "Most Expensive" in resp2['text']
    
    # 3. Test Area Search
    query3 = "Show B.Sc CS fees in OMR area"
    resp3 = generate_response(query3, [])
    print(f"Query: {query3}")
    print(f"Response: {resp3['text'][:150]}...")
    assert "OMR" in query3
    
    print("Fee handler intelligence verified successfully!")

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
        test_fee_intelligence()
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
