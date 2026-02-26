import os
import sys
import django
import re

sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.router import pre_process_query, extract_degree_level, TYPO_MAP

def test_typo_correction():
    print("\n--- Test: Typo Correction ---")
    cases = [
        ("mcc ug cources", "courses"),
        ("peri ug cources", "courses"),
        ("What are cources at loyola?", "courses"),
        ("coures at ssn", "courses"),
    ]
    for query, expected_word in cases:
        result = pre_process_query(query)
        print(f"Input:  '{query}'")
        print(f"Output: '{result}'")
        assert expected_word in result.lower(), f"Expected '{expected_word}' in '{result}'"
        print(f"✅ Typo corrected.\n")

def test_degree_level_extraction():
    print("\n--- Test: Degree Level Extraction ---")
    cases = [
        ("mcc ug courses", "UG"),
        ("peri ug courses", "UG"),
        ("ssn pg courses", "PG"),
        ("postgrad programs at loyola", "PG"),
        ("B.Tech at HITS", None),  # no explicit ug/pg keyword
    ]
    for query, expected_level in cases:
        level = extract_degree_level(query)
        print(f"Query: '{query}' -> Level: {level}")
        assert level == expected_level, f"Expected {expected_level}, got {level}"
        print("✅ Degree level extracted correctly.\n")

if __name__ == "__main__":
    try:
        test_typo_correction()
        test_degree_level_extraction()
        print("\n✨ All course routing tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
