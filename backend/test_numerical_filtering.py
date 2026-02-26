import os
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_query(query):
    print(f"\nQUERY: {query}")
    print("-" * 50)
    response = generate_response_advanced(query, [])
    
    # Check meta for intent and extraction
    meta = response.get('_meta', {})
    intent = meta.get('intent')
    extraction = meta.get('extraction', {})
    
    print(f"Detected Intent: {intent}")
    print(f"Metric: {extraction.get('target_metric')}")
    print(f"Range: {extraction.get('metric_range')}")
    print(f"Colleges Matched: {meta.get('colleges_matched')}")
    print(f"Verified: {meta.get('verified')}")
    
    # Print the first few lines of text
    first_lines = response.get('text', '').split('\n')[:8]
    print("\nRESPONSE PREVIEW:")
    print("\n".join(first_lines))
    print("=" * 60)

if __name__ == "__main__":
    queries = [
        "What colleges have 70-85% placement?",
        "Show colleges with fees under 50000",
        "Colleges with average package above 8 LPA",
        "Which college is cheapest for BCA?",
        "Compare SSN and HITS",
        "List all courses at Ethiraj"
    ]
    
    for q in queries:
        try:
            test_query(q)
        except Exception as e:
            print(f"ERROR: {e}")
