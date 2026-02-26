
import os
import sys

# isolated test for negative constraints
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response

query = "non Autonomous colleges list"
response = generate_response(query)

print(f"Query: {query}")
print("-" * 30)
print(f"Bot Response:\n{response['text']}")

# Check that HITS (non-autonomous) is in there, and Loyola (autonomous) is NOT
if "Hindustan" in response['text'] and "Loyola" not in response['text']:
    print("\n✅ PASSED: Negative constraint handled correctly.")
else:
    print("\n❌ FAILED: Still returning autonomous colleges or missing non-autonomous ones.")

# Test "not NBA"
query_nba = "list colleges that are not nba accredited"
response_nba = generate_response(query_nba)
print(f"\nQuery: {query_nba}")
print("-" * 30)
print(f"Bot Response:\n{response_nba['text']}")

# Loyola is NAAC A++ but not NBA in our data (usually)
if "Loyola" in response_nba['text']:
    print("\n✅ PASSED: 'not NBA' filter worked.")
else:
    print("\n❌ FAILED: 'not NBA' filter failed.")
