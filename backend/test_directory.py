import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response

query = "i want over all college details"
response = generate_response(query)

print(f"Query: '{query}'")
print(f"Intent: {response.get('intent')}")
print(f"Type: {response.get('type')}")
print(f"Response:\n{response.get('text')}")
