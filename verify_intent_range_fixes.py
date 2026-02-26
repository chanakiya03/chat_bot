import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_hindustan_college_alias():
    print("\n--- Issue 1: Hindustan College Alias ---")
    query = "what is the fees of bsc cs hindustan college"
    response = generate_response_advanced(query, [])
    text = response.get('text', '')
    print(f"Query: '{query}'")
    assert "Hindustan Institute" in text
    print("✅ Match found despite 'college' suffix.")

def test_loyola_shift_ii_filtering():
    print("\n--- Issue 2: Loyola Shift II Filtering ---")
    query = "Cost of M.A. Social Work at Loyola Shift II?"
    response = generate_response_advanced(query, [])
    text = response.get('text', '')
    print(f"Query: '{query}'")
    # Should NOT be a comparison table (which has pipes |)
    assert "|" not in text or "Fee Details" in text
    assert "Shift II" in text
    assert "M.A." in text
    print("✅ Shift II filtered correctly without comparison trigger.")

def test_ssn_most_expensive():
    print("\n--- Issue 3: SSN Most Expensive Intent ---")
    query = "What is the most expensive course at SSN?"
    response = generate_response_advanced(query, [])
    text = response.get('text', '')
    print(f"Query: '{query}'")
    assert "most expensive" in text.lower()
    assert "SSN College of Engineering" in text
    # Should show only the top 1 course specifically
    assert text.count("at ₹") == 1
    print("✅ SSN superlative intent forced and localized.")

def test_range_50k_currency():
    print("\n--- Issue 4: Range ₹50K Currency ---")
    query = "Courses under ₹50K?"
    response = generate_response_advanced(query, [])
    text = response.get('text', '')
    print(f"Query: '{query}'")
    assert "Colleges with Fee between 0.0 and 50000.0" in text or "under 50k" in text.lower() or "50,000" in text
    # Should be verified
    assert response.get('verified') is True
    print("✅ ₹50K parsed and verified.")

if __name__ == "__main__":
    try:
        test_hindustan_college_alias()
        test_loyola_shift_ii_filtering()
        test_ssn_most_expensive()
        test_range_50k_currency()
        print("\n✨ All bug report tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
