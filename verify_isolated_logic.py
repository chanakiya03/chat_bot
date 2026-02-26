import os
import sys
import django
import re

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.router import extract_colleges_fuzzy, match_range_regex, analyze_query_advanced, QueryAnalysis
from chatbot.engine.handlers import FeeHandler, CheapestHandler, MostExpensiveHandler
from chatbot.engine.loader import get_college_by_key

def test_alias_logic():
    print("\n--- Test: Alias Logic ---")
    raw = ["hindustan college"]
    matches = extract_colleges_fuzzy(raw)
    print(f"Input: {raw} -> Matches: {matches}")
    assert 'hindustan-institute-of-technology-and-science' in matches
    print("✅ Alias logic passed.")

def test_range_logic():
    print("\n--- Test: Range Logic ---")
    queries = [
        "Courses under ₹50K?",
        "Fees below rs 60000",
        "Packages above 8 lpa",
        "Fees between 10k and 20k"
    ]
    for q in queries:
        res = match_range_regex(q.lower())
        print(f"Query: '{q}' -> Result: {res}")
        assert res is not None
        assert 'metric_range' in res
    print("✅ Range logic passed.")

def test_intent_forcing():
    print("\n--- Test: Intent Forcing ---")
    # We can't easily test analyze_query_advanced without mocking groq, 
    # but we can verify the logic we added to it if we were to call it.
    # Instead, let's verify if the intent is correctly handled in handlers.
    pass

if __name__ == "__main__":
    try:
        test_alias_logic()
        test_range_logic()
        print("\n✨ Isolated tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
