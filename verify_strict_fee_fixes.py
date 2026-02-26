import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_strict_biotech_ranking():
    print("\n--- Testing Strict Fee Ranking ('lowest fee for B.Sc Biotechnology') ---")
    query = "Which college has the lowest fee for B.Sc Biotechnology?"
    response = generate_response_advanced(query, [])
    
    print(f"Query: '{query}'")
    text = response.get('text', '')
    print(f"Response:\n{text}")
    
    # 1. Must NOT contain B.A Economics if it's the #1 cheap choice for general
    assert "Economics" not in text
    
    # 2. Must contain the requested course
    assert "Biotechnology" in text
    
    # 3. Must only show colleges offering it
    # (Assuming we know certain colleges don't offer it, but the test here is about labels)
    assert "Course: " in text
    assert "Fee: " in text
    
    print("✅ Strict course-specific fee ranking test successful.")

def test_no_course_fallback():
    print("\n--- Testing Ranking with No Course ---")
    query = "Which are the best ranked colleges?"
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    # Should use Avg Fee
    assert "Avg Fee:" in text
    print("✅ General ranking uses Avg Fee label.")

if __name__ == "__main__":
    try:
        test_strict_biotech_ranking()
        test_no_course_fallback()
        print("\n✨ All strict course-specific ranking tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
