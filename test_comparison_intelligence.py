
import os
import sys
import json
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock Groq client
import chatbot.engine.groq_client as groq_client
groq_client.ask_groq_json = MagicMock(side_effect=[
    # Test 1: Explicit comparison
    json.dumps({"intent": "comparison", "raw_colleges": ["SSN", "HITS"], "raw_courses": ["CSE"], "is_comparison": True}),
    # Test 2: Auto-select comparison
    json.dumps({"intent": "comparison", "raw_colleges": [], "raw_courses": ["BCA"], "is_comparison": True})
])

from chatbot.engine.responder import generate_response

def test_comparison_logic():
    print("--- Testing Comparison Handler Logic ---")
    
    # 1. Test Explicit Comparison
    query1 = "Compare SSN and HITS for CSE fees"
    resp1 = generate_response(query1, [])
    print(f"Query: {query1}")
    print(f"Response: {resp1['text'][:150]}...")
    assert "Fee Comparison" in resp1['text']
    assert "SSN" in resp1['text']
    assert "Hindustan" in resp1['text']
    
    # 2. Test Auto-selection
    query2 = "Compare 2 colleges for BCA"
    resp2 = generate_response(query2, [])
    print(f"Query: {query2}")
    print(f"Response: {resp2['text'][:150]}...")
    assert "Comparison" in resp2['text']
    # Check if multiple colleges are mentioned in the response
    assert resp2['text'].count("###") >= 2 or resp2['text'].count("**") >= 4
    
    print("Comparison handler logic verified successfully!")

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
        test_comparison_logic()
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
