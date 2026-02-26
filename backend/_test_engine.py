import os
import sys
import django

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_query(query):
    print(f"\nQUERY: {query}")
    response = generate_response_advanced(query, [])
    print(f"INTENT: {response.get('intent')}")
    print(f"TYPE: {response.get('type')}")
    text = response.get('text', '')
    print(f"TEXT: {text[:200]}..." if len(text) > 200 else f"TEXT: {text}")
    return response

# Test Cases
test_query("Cheapest BCA courses")
test_query("MCC BCA fees")
test_query("What are the courses at WCC?")
test_query("Compare SSN and HITS")
test_query("Top engineering colleges")

print("\nVerification Complete!")
