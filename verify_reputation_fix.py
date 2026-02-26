
import os
import sys

# isolated test for reputation intent
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response, detect_intent

query = "What is the reputation of SSN College?"
intent = detect_intent(query)
print(f"Detected Intent: {intent}")

response = generate_response(query)
print(f"\nQuery: {query}")
print("-" * 30)
print(f"Bot Response:\n{response['text']}")
print(f"Type: {response.get('type')}")
print(f"Verified: {response.get('verified')}")

if response.get('type') == 'accreditation_direct' or response.get('type') == 'about_direct' or "reputation" in response['text'].lower() or "ranking" in response['text'].lower():
    print("\n✅ PASSED: Reputation query handled correctly.")
else:
    print("\n❌ FAILED: Reputation query still misidentified.")

# Also test WCC placement rate
query_wcc = "What is the placement of WCC?"
response_wcc = generate_response(query_wcc)
print(f"\nQuery: {query_wcc}")
print("-" * 30)
print(f"Bot Response:\n{response_wcc['text']}")
if "35%" in response_wcc['text']:
    print("\n✅ PASSED: WCC placement rate updated correctly.")
else:
    print("\n❌ FAILED: WCC placement rate not updated (Check conver.py or data).")
