
import os
import sys

# isolated test for context hijacking
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response

# Simulate context: Last discussed college was HITS
history = [
    {"role": "user", "content": "Tell me about HITS"},
    {"role": "assistant", "content": "Hindustan Institute of Technology and Science (HITS) is a Deemed University... [hits]"}
]

query = "Autonomous colleges list"
response = generate_response(query, context_history=history)

print(f"Query: {query}")
print("-" * 30)
print(f"Bot Response:\n{response['text']}")
print(f"Type: {response.get('type')}")

if response.get('type') == 'accreditation_filter' and "Autonomous" in response['text'] and "Hindustan" not in response['text'].split('\n')[0]:
    print("\n✅ PASSED: Context hijacking prevented. Global list returned.")
else:
    print("\n❌ FAILED: Context still hijacking the query or wrong response type.")
