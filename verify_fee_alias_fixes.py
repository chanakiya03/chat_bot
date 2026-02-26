import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_cross_college_fee_range():
    print("\n--- Testing Cross-College Fee Range ('Courses under 50k') ---")
    # History includes BCA to test bleed prevention
    history = [{"role": "user", "content": "Tell me about BCA at Loyola"}, {"role": "assistant", "content": "..."}]
    query = "Courses under 50k?"
    response = generate_response_advanced(query, history)
    
    print(f"Query: '{query}'")
    print(f"Intent: {response.get('_meta', {}).get('intent')}")
    print(f"Type: {response.get('type')}")
    
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    assert response.get('type') == 'cross_college_fee_range'
    assert "BCA" not in text or "BCA" in query # Should not be dominated by BCA if it's a general search
    print("✅ Cross-college fee range successful.")

def test_hits_acronym_and_btech_be():
    print("\n--- Testing HITS Acronym and B.Tech/B.E Mapping ---")
    query = "B.Tech fees at HITS?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if HITS was mapped correctly (look for Hindustan in response)
    assert "Hindustan" in text or "HITS" in text
    assert "B.E" in text or "B.Tech" in text
    assert "couldn't retrieve" not in text.lower()
    print("✅ HITS acronym and B.Tech mapping successful.")

def test_cheapest_ranking_intent():
    print("\n--- Testing 'Which college is cheapest?' Intent ---")
    query = "Which college is cheapest?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    print(f"Intent: {response.get('_meta', {}).get('intent')}")
    print(f"Type: {response.get('type')}")
    
    assert response.get('_meta', {}).get('intent') == 'ranking'
    assert "Affordable" in response.get('text', '')
    print("✅ Cheapest ranking intent successful.")

if __name__ == "__main__":
    try:
        test_cross_college_fee_range()
        test_hits_acronym_and_btech_be()
        test_cheapest_ranking_intent()
        print("\n✨ All bug fixes verified!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
