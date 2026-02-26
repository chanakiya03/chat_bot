import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_lowest_fee_biotech():
    print("\n--- Testing Course-Specific Fee Ranking ('lowest fee for B.Sc Biotechnology') ---")
    query = "Which college has the lowest fee for B.Sc Biotechnology?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response:\n{text}")
    
    # Check for specific course info in ranking
    assert "B.Sc Biotechnology" in text or "biotechnology" in text.lower()
    assert "Fee:" in text
    assert "Avg Fee:" not in text or "Course:" in text # Should favor Course: [Name]
    print("✅ Course-specific fee ranking test successful.")

def test_cheapest_bca():
    print("\n--- Testing Cheapest BCA Ranking ---")
    query = "Cheapest college for BCA?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response snippet:\n{text[:300]}...")
    
    assert "BCA" in text
    assert "Fee:" in text
    print("✅ Cheapest BCA test successful.")

if __name__ == "__main__":
    try:
        test_lowest_fee_biotech()
        test_cheapest_bca()
        print("\n✨ All course-specific fee ranking tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
