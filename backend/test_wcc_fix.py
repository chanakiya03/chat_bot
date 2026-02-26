"""Targeted test for WCC B.Com fees query."""
import os
import sys
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')

import django
django.setup()

from chatbot.engine.responder import generate_response_advanced
from chatbot.engine.router import analyze_query_advanced, extract_colleges_fuzzy

def clean_for_terminal(text):
    """Strip non-ASCII characters for clean printing in Windows CMD."""
    return text.encode('ascii', 'ignore').decode('ascii')

query = "WCC B.Com fees?"
print(f"Testing Query: {query}")

# 1. Component Level Check: Acronym Matching
raw_colleges = ["WCC"]
matched = extract_colleges_fuzzy(raw_colleges)
print(f"  Fuzzy Match for {raw_colleges}: {matched}")
if matched == ['womens-christian-college']:
    print("  OK: Acronym Matching: PASSED")
else:
    print(f"  FAIL: Acronym Matching: FAILED (Got {matched})")

# 2. End-to-End Orchestrator Check
response = generate_response_advanced(query, [])
text = response.get('text', '')
print("\nResponse Text (Sanitized for Terminal):")
print("-" * 20)
print(clean_for_terminal(text))
print("-" * 20)

if "Women's Christian College" in text and "B.Com" in text:
    # Check if other courses (like B.A. Economics) are NOT in the text
    # Note: B.A Economics appears in Ethiraj's table which the user reported
    if "B.A Economics" not in text and "Ethiraj" not in text:
        print("\nOK: End-to-End: PASSED (Correct college and specific course filter)")
    else:
        print("\nFAIL: End-to-End: FAILED (Course filtering not applied or wrong college showed up)")
else:
    print(f"\nFAIL: End-to-End: FAILED (Wrong college or course not found. text was: {text[:100]}...)")
