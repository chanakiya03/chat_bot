
import os
import sys

# isolated test for comparison fix
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
        print(f"Bot Response:\n{response['text']}")
        print(f"Intent: {response.get('intent')}")
        print(f"Type: {response.get('type')}")
        return response
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

# The user's specific query
run_test("Which college is cheaper for M.A. HRM, Ethiraj or WCC?")
