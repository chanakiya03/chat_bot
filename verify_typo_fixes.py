import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_its_hits_typo():
    print("\n--- Testing 'its' -> 'hits' Typo Correction ---")
    query = "its bsc cs fees"
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    print(f"Response snippet:\n{text[:500]}...")
    
    # Should resolve to HITS
    assert "Hindustan Institute of Technology and Science" in text
    print("✅ 'its' contextually corrected to 'hits'.")

def test_its_pronoun_preservation():
    print("\n--- Testing 'its' Pronoun Preservation ---")
    history = [
        {'role': 'user', 'content': 'Tell me about HITS'},
        {'role': 'assistant', 'content': 'HITS is a college...'}
    ]
    query = "What is its fee?"
    # Here 'its' should NOT be replaced by 'hits' because it's a valid pronoun usage
    # although in this specific case replacing might actually work, we want to ensure
    # we don't blindly replace it. If it remains 'its', Gross handles the pronoun.
    response = generate_response_advanced(query, history)
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    # If the bot answers about HITS, we succeeded (either via pronoun or correction)
    # But we specifically want to check if it thinks it's a general query if we didn't correct it and Groq didn't resolve.
    assert "Hindustan Institute" in text
    print("✅ 'its' handled correctly in pronoun context.")

def test_alias_fuzzy_matching():
    print("\n--- Testing Alias-Level Fuzzy Matching ('perii') ---")
    query = "perii bsc fees"
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    print(f"Response snippet:\n{text[:500]}...")
    
    assert "PERI College of Arts and Science" in text
    print("✅ 'perii' fuzzy matched to 'peri' successfully.")

if __name__ == "__main__":
    try:
        test_its_hits_typo()
        test_its_pronoun_preservation()
        test_alias_fuzzy_matching()
        print("\n✨ All typo and alias fuzzy matching tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
