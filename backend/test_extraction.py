import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import extract_college_names
from chatbot.engine.loader import get_all_colleges

colleges = get_all_colleges()
print(f"Loaded {len(colleges)} colleges.")
for c in colleges:
    print(f"- {c['name']} (Key: {c['key']})")

test_queries = [
    "Tell me about MCC",
    "Tell me about WCC",
    "Tell me about HITS",
    "Tell me about Loyola",
    "Tell me about Ethiraj",
    "Tell me about PERI",
    "Tell me about Hindustan"
]

print("\n--- Testing Name Extraction ---")
for q in test_queries:
    matches = extract_college_names(q)
    print(f"Query: '{q}' -> Matches: {matches}")
