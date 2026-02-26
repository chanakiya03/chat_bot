import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

# Mock Django settings if needed, but for utils it might not be necessary
# unless it imports settings or models.
# Based on previous view_file, utils.py imports some things.

from chatbot.engine.utils import extract_course, _normalize

def test_extraction(query):
    extracted = extract_course(query)
    norm = _normalize(extracted) if extracted else None
    print(f"Query: {query}")
    print(f"Extracted: {extracted}")
    print(f"Normalized: {norm}")
    print("-" * 20)

test_extraction("hits btech ai and ml")
test_extraction("BCA course at MCC")
test_extraction("MBA fees at SSN")
