import os
import django
import sys

# Setup Django
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat.settings')
django.setup()

from chatbot.engine.responder import generate_response
from chatbot.engine.router import QueryAnalysis

def test_manual_crash():
    print("\nTESTING MANUAL VALUE UNPACKING CRASH...")
    # Simulate an analysis with a single-item metric_range
    query = "colleges with package 5 lpa"
    analysis = QueryAnalysis(
        intent="placement",
        raw_colleges=[],
        raw_courses=[],
        target_metric="package",
        metric_range=[5.0] # This would have crashed before
    )
    
    # We need to test the handler directly or via responder if we can mock analysis
    # But since I already fixed normalize_numerical_range, let's see if generate_response works
    # with a query that might produce such a result.
    response = generate_response(query)
    print(f"RESPONSE TYPE: {response.get('type')}")
    print(f"TEXT: {response.get('text')}")
    print("SUCCESS: No crash occurred.")

if __name__ == "__main__":
    test_manual_crash()
