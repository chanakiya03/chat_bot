
import os
import sys

# isolated test for strict name matching and details view
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response, extract_college_names

def run_test(query):
    print(f"\nQuery: {query}")
    keys = extract_college_names(query)
    print(f"Extracted Keys: {keys}")
    
    response = generate_response(query)
    print("-" * 30)
    print(f"Bot Response:\n{response['text']}")
    return response

# Test 1: Exact Name Match with potentially colliding words
run_test("Women’s Christian College details")

# Test 2: MCC specifically
run_test("Madras Christian College info")

# Test 3: Not found
run_test("Harvard University details")

# Test 4: Comparison still works
run_test("Compare WCC and MCC")
