
import os
import sys

# isolated test for name matching collision
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response, extract_college_names

query = "Ethiraj College for Women details"
keys = extract_college_names(query)
print(f"Query: {query}")
print(f"Extracted Keys: {keys}")

response = generate_response(query)
print("-" * 30)
print(f"Bot Response:\n{response['text']}")

# Verification
if len(keys) == 1 and keys[0] == 'ethiraj':
    print("\n✅ PASSED: Name matching isolated to Ethiraj.")
elif 'ethiraj' in keys and 'wcc' in keys:
    print("\n❌ FAILED: Still returning both Ethiraj and WCC.")
else:
    print(f"\n❓ UNEXPECTED result: {keys}")
    
# Test WCC specifically
query_wcc = "Tell me about WCC"
keys_wcc = extract_college_names(query_wcc)
print(f"\nQuery: {query_wcc}")
print(f"Extracted Keys: {keys_wcc}")
if 'wcc' in keys_wcc:
    print("✅ PASSED: WCC still identifiable by abbreviation.")
