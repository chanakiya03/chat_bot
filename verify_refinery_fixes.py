import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_mcc_alias_and_ug_filter():
    print("\n--- Testing MCC Alias and UG Filter ('MCC UG courses') ---")
    query = "MCC UG courses"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if MCC was mapped (look for Madras Christian College in response)
    assert "Madras Christian College" in text
    # Check if only B. courses are listed
    import re
    found_m_courses = re.findall(r"\bM\.", text)
    found_b_courses = re.findall(r"\bB\.", text)
    print(f"Found B. courses: {len(found_b_courses)}, M. courses: {len(found_m_courses)}")
    
    assert len(found_b_courses) > 0
    assert len(found_m_courses) == 0
    print("✅ MCC alias and UG filter successful.")

def test_global_facility_search():
    print("\n--- Testing Global Facility Search ('Which college mentions a Science Forum club?') ---")
    # History includes WCC to test bleed prevention
    history = [{"role": "user", "content": "Tell me about WCC"}, {"role": "assistant", "content": "..."}]
    query = "Which college mentions a Science Forum club?"
    response = generate_response_advanced(query, history)
    
    print(f"Query: '{query}'")
    print(f"Intent: {response.get('_meta', {}).get('intent')}")
    print(f"Type: {response.get('type')}")
    
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # WCC does have a Science Forum, but MCC also has it. 
    # The key is that it shouldn't just be WCC if it's a global search.
    assert response.get('type') == 'global_facility_search'
    # Check if multiple colleges are returned or at least it found a match
    assert "Colleges mentioning 'Science Forum'" in text
    print("✅ Global facility search successful.")

if __name__ == "__main__":
    try:
        test_mcc_alias_and_ug_filter()
        test_global_facility_search()
        print("\n✨ All refinery bug fixes verified!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
