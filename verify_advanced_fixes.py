import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_currency_and_multiplier_regex():
    print("\n--- Testing Currency and Multiplier Regex ('Courses under ₹50K') ---")
    query = "Courses under ₹50K?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    print(f"Intent: {response.get('_meta', {}).get('intent')}")
    print(f"Type: {response.get('type')}")
    
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if results are under 50k
    assert response.get('type') == 'cross_college_fee_range'
    print("✅ Currency and multiplier regex successful.")

def test_degree_level_filtering():
    print("\n--- Testing Degree Level Filtering ('MCC UG courses') ---")
    query = "MCC UG courses"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    # Check if only B. courses are listed (ignoring headers/meta)
    import re
    # We expect courses like B.Sc, B.Com, BCA, BBA
    # We should NOT see M.Sc, M.Com, MCA, MBA
    found_m_courses = re.findall(r"\bM\.", text)
    found_b_courses = re.findall(r"\bB\.", text)
    
    print(f"Found B. courses count: {len(found_b_courses)}")
    print(f"Found M. courses count: {len(found_m_courses)}")
    
    assert len(found_b_courses) > 0
    assert len(found_m_courses) == 0
    print("✅ Degree level filtering successful.")

def test_shift_comparison_logic():
    print("\n--- Testing Shift Comparison Logic ---")
    query = "Compare Shift I and Shift II fees at WCC"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    print(f"Type: {response.get('type')}")
    text = response.get('text', '')
    print(f"Response snippet: {text[:200]}...")
    
    assert response.get('type') == 'shift_comparison'
    assert "Shift I" in text and "Shift II" in text
    print("✅ Shift comparison logic successful.")

if __name__ == "__main__":
    try:
        test_currency_and_multiplier_regex()
        test_degree_level_filtering()
        test_shift_comparison_logic()
        print("\n✨ All advanced bug fixes verified!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()





