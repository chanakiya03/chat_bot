
import os
import sys

# isolated test for 500 error fix
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response

def run_test(query):
    print(f"\nQuery: {query}")
    try:
        response = generate_response(query)
        print("-" * 30)
        print(f"Bot Response:\n{response['text'][:100]}...")
        print(f"Type: {response.get('type')}")
        return response
    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()
        return None

# Test 1: Broad query that previously crashed
run_test("over all college deatils")

# Test 2: Specific query that should still work
run_test("PERI over all details")

# Test 3: Standard directory query
run_test("overall directory")
