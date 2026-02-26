import os
import django
import sys

# Setup Django
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat.settings')
django.setup()

from chatbot.engine.responder import generate_response
from chatbot.engine.router import analyze_query_advanced

def test_query(query):
    print(f"\nQUERY: {query}")
    response = generate_response(query)
    print(f"INTENT: {response.get('_meta', {}).get('intent')}")
    print(f"COLLEGES MATCHED: {response.get('_meta', {}).get('colleges_matched')}")
    print(f"TYPE: {response.get('type')}")
    print(f"RESPONSE:\n{response.get('text')}\n")
    return response

if __name__ == "__main__":
    # Test 1: Punctuation Handling
    test_query("HITS?")
    
    # Test 2: Multi-College with Conjunction
    test_query("WCC vs MCC")
    
    # Test 3: Horizontal Comparison Table
    test_query("HITS vs SSN fees")
    
    # Test 4: Global Cheapest Fallback
    test_query("Which college is cheapest?")
    
    # Test 5: Attribute Search Routing & Handling
    test_query("Which college has NBA accreditation?")
    test_query("Show autonomous colleges")
