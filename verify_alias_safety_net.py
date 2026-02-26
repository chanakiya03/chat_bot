import os
import sys
import django

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_chat_backend.settings')
django.setup()

from chatbot.engine.responder import generate_response_advanced

def test_alias_safety_net():
    print("\n--- Testing Alias Safety Net ('hits bsc cs fees') ---")
    # We simulate a scenario where we want to ensure HITS is caught regardless of LLM
    query = "hits bsc cs fees"
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    print(f"Response snippet:\n{text[:500]}...")
    
    assert "Hindustan Institute of Technology and Science" in text
    assert "B.Sc Computer Science" in text
    print("✅ Alias 'hits' caught via Safety Net.")

def test_peri_safety_net():
    print("\n--- Testing Alias Safety Net ('peri bsc cs fees') ---")
    query = "peri bsc cs fees"
    response = generate_response_advanced(query, [])
    
    text = response.get('text', '')
    print(f"Query: '{query}'")
    print(f"Response snippet:\n{text[:500]}...")
    
    assert "PERI College of Arts and Science" in text
    print("✅ Alias 'peri' caught via Safety Net.")

if __name__ == "__main__":
    try:
        test_alias_safety_net()
        test_peri_safety_net()
        print("\n✨ All alias safety net tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
