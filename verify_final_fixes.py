import sys
import os

# Set up Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
import django
django.setup()

from chatbot.engine.utils import autocorrect_query
from chatbot.engine.router import analyze_query_advanced
from chatbot.engine.responder import generate_response_advanced

def test_spell_correction():
    queries = [
        "wat is the placment feese at hits",
        "MCC admision criteria?",
        "Compare SSN and HITS for B.Tech",
        "What are the hostal facilities?"
    ]
    
    print("\n--- Testing Spell Correction ---")
    for q in queries:
        corrected = autocorrect_query(q)
        print(f"Original: '{q}'\nCorrected: '{corrected}'\n")

def test_responder_import():
    print("\n--- Testing Responder Import & Pipeline ---")
    try:
        # Simple query to trigger generation
        # We use a mock history
        history = [{"role": "user", "content": "hi"}]
        # This will test if the import error still exists in generate_response_advanced
        # and if the verifier logic works with raw dictionaries
        response = generate_response_advanced("tell me about SSN", history)
        print("Response generated successfully!")
        print(f"Text snippet: {response.get('text', '')[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spell_correction()
    test_responder_import()
