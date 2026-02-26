
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat.settings')
django.setup()

from chatbot.engine.responder import extract_college_names, detect_intent, generate_response

query = "Are Loyola and WCC in the same locality?"
colleges = extract_college_names(query)
intent = detect_intent(query)
response = generate_response(query)

print(f"Query: {query}")
print(f"Detected Intent: {intent}")
print(f"Extracted Colleges: {colleges}")
print("-" * 30)
print(f"Bot Response:\n{response['text']}")
