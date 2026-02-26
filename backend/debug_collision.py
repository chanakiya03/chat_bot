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

query = "Admission criteria for HITS"
matches = extract_college_names(query)
print(f"\nQuery: '{query}'")
print(f"Matches: {matches}")

for m in matches:
    c = next((col for col in colleges if col['key'] == m), None)
    if c:
        print(f"Match: {c['name']} (Key: {c['key']})")
        # Check why it matched
        name_clean = re_sub = __import__('re').sub(r'[()]', ' ', c['name'].lower())
        name_parts = [n.strip() for n in name_clean.split() if n.strip()]
        print(f"  Name Parts: {name_parts}")
