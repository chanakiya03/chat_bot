
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat.settings')
django.setup()

from chatbot.engine.responder import generate_response, detect_intent

query = ["Colleges in Egmore","Nungambakkam colleges","tambaram college",,"Which is on OMR?","Colleges in Egmore"]
intent = detect_intent(query)
response = generate_response(query)

print(f"Query: {query}")
print(f"Detected Intent: {intent}")
print("-" * 30)
print(f"Bot Response:\n{response['text']}")
print(f"Response Type: {response.get('type')}")
print(f"Verified: {response.get('verified')}")
if 'sources' in response:
    print(f"Sources: {response['sources']}")
