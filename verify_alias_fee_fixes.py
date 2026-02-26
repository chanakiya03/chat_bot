import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_alias_matching():
    print("\n--- Testing Alias Matching ('Hindustan bsc cs fees') ---")
    query = "Hindustan bsc cs fees"
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    print(f"Response snippet:\n{text[:500]}...")
    
    # Check if HITS is matched (look for the name in the output)
    assert "Hindustan Institute of Technology and Science" in text
    assert "B.Sc Computer Science" in text
    print("✅ Alias 'Hindustan' matched successfully.")

def test_college_not_found_error():
    print("\n--- Testing College Not Found Error ---")
    # Using a name that definitely shouldn't be matched by Groq or Fuzzy
    query = "What are the fees at Hogwarts?" 
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    print(f"Response: {text}")
    
    assert "❌ I couldn't identify the college" in text
    print("✅ Granular college not found error verified.")

def test_course_not_found_error():
    print("\n--- Testing Course Not Found at College Error ---")
    query = "HITS fee for B.A. Bharathanatyam" # Likely not offered at HITS
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    print(f"Response: {text}")
    
    assert "Hindustan Institute of Technology and Science" in text
    assert "couldn't find fee data for B.A. BHARATHANATYAM" in text or "couldn't find fee data for" in text
    print("✅ Granular course not found error verified.")

if __name__ == "__main__":
    try:
        test_alias_matching()
        test_college_not_found_error()
        test_course_not_found_error()
        print("\n✨ All alias and fee error fixes passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
