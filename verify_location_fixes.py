import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_location_adyar():
    print("\n--- Testing Location Search ('Colleges in Adyar?') ---")
    query = "Colleges in Adyar?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if Adyar colleges are found
    assert "📍 Colleges located in/near Adyar" in text
    assert "Patrician College" in text or "sources" in response
    print("✅ Adyar location test successful.")

def test_location_omr():
    print("\n--- Testing Location Search ('Which is on OMR?') ---")
    query = "Which is on OMR?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if OMR colleges are found
    assert "📍 Colleges located in/near Omr" in text
    # Should include colleges like SSN, HITS, Jeppiaar if they have OMR-related locations in DB
    print("✅ OMR location test successful.")

def test_autonomous_ranking():
    print("\n--- Testing Autonomous Ranking Title ---")
    query = "Best autonomous college?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if the title is dynamic
    assert "🏆 Top Ranked Autonomous Colleges" in text
    print("✅ Autonomous ranking title test successful.")

if __name__ == "__main__":
    try:
        test_location_adyar()
        test_location_omr()
        test_autonomous_ranking()
        print("\n✨ All location and autonomous verification tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        # import traceback
        # traceback.print_exc()
