
import os
import sys

# Standard mock to avoid DB hang/issues if possible, but loader might still trigger it
# Let's try to run with the actual loader since I fixed it (Robust Hybrid Loader)
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response
from chatbot.engine.loader import load_knowledge_base

# Force reload to ensure my changes are picked up
load_knowledge_base(force_reload=True)

query = "Which college has the highest fee for B.A. Economics?"
response = generate_response(query)

print(f"Query: {query}")
print("-" * 30)
print(f"Bot Response:\n{response['text']}")

# Check for duplicates in text
lines = response['text'].split('\n')
college_names = []
duplicates = []
for line in lines:
    if ". " in line and "(" in line:
        name = line.split(". ")[1].split(" (")[0].strip()
        if name in college_names:
            duplicates.append(name)
        college_names.append(name)

if duplicates:
    print(f"\n❌ FAILED: Duplicates found: {duplicates}")
else:
    print("\n✅ PASSED: No duplicates found.")
