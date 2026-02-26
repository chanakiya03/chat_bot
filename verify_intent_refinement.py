import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_greeting_bypass():
    print("\n--- Testing Greeting Bypass ---")
    query = "hello"
    response = generate_response_advanced(query, [])
    print(f"Query: '{query}'")
    print(f"Intent: {response.get('_meta', {}).get('intent')}")
    print(f"Text snippet: {response.get('text')[:100]}...")
    assert response.get('_meta', {}).get('intent') == 'greeting'
    print("✅ Greeting bypass successful.")

def test_superlative_override():
    print("\n--- Testing Superlative Intent Override ---")
    query = "Best colleges?"
    response = generate_response_advanced(query, [])
    print(f"Query: '{query}'")
    print(f"Intent: {response.get('_meta', {}).get('intent')}")
    assert response.get('_meta', {}).get('intent') == 'ranking'
    print("✅ Superlative override successful.")

def test_autonomous_filtering():
    print("\n--- Testing Autonomous Filtering ---")
    query = "Best autonomous college?"
    response = generate_response_advanced(query, [])
    print(f"Query: '{query}'")
    print(f"Intent: {response.get('_meta', {}).get('intent')}")
    text = response.get('text', '')
    
    # Check if colleges listed are indeed autonomous
    from chatbot.engine.loader import get_all_colleges
    all_colleges = {c['name']: c for c in get_all_colleges()}
    
    import re
    college_names = re.findall(r'\*\*[\d]+\.\s*([^*]+)\*\*', text)
    print(f"Colleges found: {college_names}")
    
    for name in college_names:
        # Fuzzy match name to find college
        found = False
        for c_name, c_data in all_colleges.items():
            if name.strip().lower() in c_name.lower():
                inst_type = c_data['details'].get('Type', '')
                print(f"Verifying {c_name}: Type='{inst_type}'")
                assert 'autonomous' in inst_type.lower()
                found = True
                break
        if not found:
            print(f"⚠️ Could not verify type for '{name}' (fuzzy match failed)")
            
    assert response.get('_meta', {}).get('intent') == 'ranking'
    print("✅ Autonomous filtering successful.")

if __name__ == "__main__":
    try:
        test_greeting_bypass()
        test_superlative_override()
        test_autonomous_filtering()
        print("\n✨ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
